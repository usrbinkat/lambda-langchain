import pulumi
import pulumi_azure_native as azure
import pulumi_azure_native.resources as azure_resources
import pulumi_synced_folder as synced

# Import the program's configuration settings.
config = pulumi.Config()
www_path = config.get("sitePath", "./www")
app_path = config.get("appPath", "./app")
index_document = config.get("indexDocument", "index.html")
error_document = config.get("errorDocument", "error.html")

# Create a resource group for the website.
resource_group = azure.resources.ResourceGroup("resource-group")

# Create a blob storage account.
account = azure.storage.StorageAccount(
    "account",
    resource_group_name=resource_group.name,
    kind="StorageV2",
    sku=azure.storage.SkuArgs(
        name="Standard_LRS",
    ),
)

# Create a storage container for the pages of the website.
website = azure.storage.StorageAccountStaticWebsite(
    "website",
    account_name=account.name,
    resource_group_name=resource_group.name,
    index_document=index_document,
    error404_document=error_document,
)

# Use a synced folder to manage the files of the website.
synced_folder = synced.AzureBlobFolder(
    "synced-folder",
    path=www_path,
    resource_group_name=resource_group.name,
    storage_account_name=account.name,
    container_name=website.container_name,
)

# Create a storage container for the serverless app.
app_container = azure.storage.BlobContainer(
    "app-container",
    account_name=account.name,
    resource_group_name=resource_group.name,
    public_access=azure.storage.PublicAccess.NONE,
)

# Upload the serverless app to the storage container.
app_blob = azure.storage.Blob(
    "app-blob",
    account_name=account.name,
    resource_group_name=resource_group.name,
    container_name=app_container.name,
    source=pulumi.FileArchive(app_path),
)

# Create a shared access signature to give the Function App access to the code.
sas_token = (
    pulumi.Output.all(resource_group.name, account.name, app_container.name, app_blob.name)
    .apply(
        lambda args: azure.storage.list_storage_account_service_sas(
            resource_group_name=args[0],
            account_name=args[1],
            protocols="https",
            shared_access_start_time="2022-01-01",
            shared_access_expiry_time="2030-01-01",
            resource="b",
            permissions="r",
            canonicalized_resource=f"/blob/{args[1]}/{args[2]}",
            content_disposition=None,
            content_encoding=None,
            content_language=None,
            content_type=None,
            ip=None,
            key_to_sign=None,
            cache_control=None,
        )
    )
    .apply(lambda result: result.service_sas_token)
)

# Create an App Service plan for the Function App.
plan = azure.web.AppServicePlan(
    "plan",
    resource_group_name=resource_group.name,
    kind="Linux",
    reserved=True,
    sku=azure.web.SkuDescriptionArgs(
        name="Y1",
        tier="Dynamic",
    ),
)

# Fetch OpenAI API Token from Pulumi Config
openai_token = config.get_secret("openaiToken")

# Export the primary key of the Storage Account
primary_key = (
    pulumi.Output.all(resource_group.name, account.name)
    .apply(
        lambda args: azure.storage.list_storage_account_keys(
            resource_group_name=args[0], account_name=args[1]
        )
    )
    .apply(lambda accountKeys: accountKeys.keys[0].value)
)

# Create the Function App.
app = azure.web.WebApp(
    "app",
    resource_group_name=resource_group.name,
    server_farm_id=plan.id,
    kind="FunctionApp",
    site_config=azure.web.SiteConfigArgs(
        app_settings=[
            azure.web.NameValuePairArgs(
                name="FUNCTIONS_WORKER_RUNTIME",
                value="python",
            ),
            azure.web.NameValuePairArgs(
                name="FUNCTIONS_EXTENSION_VERSION",
                value="~4",
            ),
            azure.web.NameValuePairArgs(
                name="WEBSITE_RUN_FROM_PACKAGE",
                value=pulumi.Output.all(account.name, app_container.name, app_blob.name, sas_token).apply(
                    lambda args: f"https://{args[0]}.blob.core.windows.net/{args[1]}/{args[2]}?{args[3]}"
                ),
            ),
            azure.web.NameValuePairArgs(
                name="OPENAI_API_KEY",
                value=openai_token,
            ),
            azure.web.NameValuePairArgs(
                name="AzureWebJobsStorage",
                value=pulumi.Output.all(account.name, primary_key).apply(lambda args: f"DefaultEndpointsProtocol=https;AccountName={args[0]};AccountKey={args[1]};EndpointSuffix=core.windows.net"),
            ),
        ],
        cors=azure.web.CorsSettingsArgs(
            allowed_origins=["*"],
        ),
    ),
)

## Create an API Management service
#api_management_service = azure.apimanagement.ApiManagementService(
#    "api-management-service",
#    resource_group_name=resource_group.name,
#    publisher_email="email@yourcompany.com",
#    publisher_name="yourcompany",
#    sku=azure_resources.SkuArgs( # The SKU of the Api Management Service
#        name="Developer",
#        capacity=1,
#    ),
#)
# Create an API Management service
api_management_service = azure.apimanagement.ApiManagementService(
    "api-management-service",
    resource_group_name=resource_group.name,
    publisher_email="emcee@mlapps.com",
    publisher_name="mlapps",
    sku=azure_resources.SkuArgs( # The SKU of the Api Management Service
        name="Developer",
        capacity=1,
    ),
    enable_client_certificate=True,  # Enable client certificate
)

# Create an API Management API operations
api_management_api = azure.apimanagement.Api(
    "api-management-api",
    resource_group_name=resource_group.name,
    display_name="API Management API",
    path="api",
    protocols=["https"],
    service_name=api_management_service.name,
)

# Create a product for the API operations
product = azure.apimanagement.Product(
    "product",
    resource_group_name=resource_group.name,
    product_id="unlimited",
    service_name=api_management_service.name,
    display_name=api_management_service.name,
)

# Add API to the product
product_api = azure.apimanagement.ProductApi(
    "product-api",
    api_id=api_management_api.api_id,
    product_id=product.product_id,
    resource_group_name=resource_group.name,
    service_name=api_management_service.name,
)

# Export the URLs of the website and serverless endpoint.
pulumi.export("siteURL", account.primary_endpoints.apply(lambda ep: ep.web))
pulumi.export("apiManagementURL", api_management_service.gateway_url)
