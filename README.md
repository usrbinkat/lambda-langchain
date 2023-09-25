# LangChain Serverless Bot

```bash
~/Git/pulumi/langchain  main 18s langchain ❯ pulumi up
Updating (azfunc)

View in Browser (Ctrl+O): https://app.pulumi.com/usrbinkat/t/azfunc/updates/23

     Type                                                 Name                      Status
 +   pulumi:pulumi:Stack                                  t-azfunc                  created (51s)
 +   ├─ azure-native:resources:ResourceGroup              resource-group            created (0.49s)
 +   ├─ azure-native:web:AppServicePlan                   plan                      created (2s)
 +   ├─ azure-native:storage:StorageAccount               account                   created (20s)
 +   ├─ azure-native:storage:StorageAccountStaticWebsite  website                   created (1s)
 +   ├─ azure-native:storage:BlobContainer                app-container             created (0.77s)
 +   ├─ azure-native:storage:Blob                         app-blob                  created (0.52s)
 +   ├─ synced-folder:index:AzureBlobFolder               synced-folder             created (0.26s)
 +   │  ├─ azure-native:storage:Blob                      synced-folder-error.html  created (0.94s)
 +   │  └─ azure-native:storage:Blob                      synced-folder-index.html  created (0.96s)
 +   ├─ azure-native:web:WebApp                           app                       created (24s)
 +   └─ azure-native:storage:Blob                         config.json               created (0.58s)


Outputs:
    apiURL : "https://app0a14a1db.azurewebsites.net/api"
    siteURL: "https://account8217ccf3.z5.web.core.windows.net/"

Resources:
    + 12 created

Duration: 54s
```




