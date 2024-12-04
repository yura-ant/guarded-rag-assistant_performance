# Guarded RAG Assistant

The guarded RAG assistant is an easily customizable recipe for building a RAG-powered chatbot. 

In addition to creating a hosted, shareable user interface, the guarded RAG assistant provides:

* Business logic and LLM-based guardrails.
* A predictive secondary model that evaluates response quality.
* GenAI-focused [custom metrics][custom-metrics].
* DataRobot MLOps hosting, monitoring, and governing the individual back-end deployments.

> [!WARNING]
> Application templates are intended to be starting points that provide guidance on how to develop, serve, and maintain AI applications.
> They require a developer or data scientist to adapt and modify them for their business requirements before being put into production.

![Using the Guarded RAG Assistant](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/launch_gifs/guardedraghq-small.gif)

[custom-metrics]: https://docs.datarobot.com/en/docs/workbench/nxt-console/nxt-monitoring/nxt-custom-metrics.html

## Table of contents
1. [Setup](#setup)
2. [Architecture overview](#architecture-overview)
3. [Why build AI Apps with DataRobot app templates?](#why-build-ai-apps-with-datarobot-app-templates)
4. [Make changes](#make-changes)
   - [Change the RAG documents](#change-the-rag-documents)
   - [Change the LLM](#change-the-llm)
   - [Custom front-end](#fully-custom-front-end)
   - [Custom RAG logic](#fully-custom-rag-chunking-vectorization-and-retrieval)
5. [Share results](#share-results)
6. [Delete all resources](#delete-all-provisioned-resources)
7. [Setup for advanced users](#setup-for-advanced-users)
8. [Data privacy](#data-privacy)


## Setup

> [!IMPORTANT]  
> If you are running this template in a DataRobot codespace, `pulumi` is already configured and the repo is automatically cloned;
> skip to **Step 3**.
1. If `pulumi` is not already installed, install the CLI following instructions [here](https://www.pulumi.com/docs/iac/download-install/). 
   After installing for the first time, restart your terminal and run:
   ```bash
   pulumi login --local  # omit --local to use Pulumi Cloud (requires separate account)
   ```

2. Clone the template repository.

   ```bash
   git clone https://github.com/datarobot-community/guarded-rag-assistant.git
   cd guarded-rag-assistant
   ```

3. Rename the file `.env.template` to `.env` in the root directory of the repo and populate your credentials.
   This template is pre-configured to use an Azure OpenAI endpoint. If you wish to use a different LLM provider, modifications to the code will be [necessary](#change-the-llm).

   ```bash
   DATAROBOT_API_TOKEN=...
   DATAROBOT_ENDPOINT=...  # e.g. https://app.datarobot.com/api/v2
   OPENAI_API_KEY=...
   OPENAI_API_VERSION=...  # e.g. 2024-02-01
   OPENAI_API_BASE=...  # e.g. https://your_org.openai.azure.com/
   OPENAI_API_DEPLOYMENT_ID=...  # e.g. gpt-4
   PULUMI_CONFIG_PASSPHRASE=...  # required, choose your own alphanumeric passphrase to be used for encrypting pulumi config
   ```
   Use the following resources to locate the required credentials:
   - **DataRobot API token**: Refer to the *Create a DataRobot API Key* section of the [DataRobot API Quickstart guide](https://docs.datarobot.com/en/docs/api/api-quickstart/index.html#create-a-datarobot-api-key).
   - **DataRobot endpoint**: Refer to the *Retrieve the API Endpoint* section of the [DataRobot API Quickstart guide](https://docs.datarobot.com/en/docs/api/api-quickstart/index.html#retrieve-the-api-endpoint).
   - **LLM endpoint and API key**: Refer to the [Azure OpenAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/chatgpt-quickstart?tabs=command-line%2Cjavascript-keyless%2Ctypescript-keyless%2Cpython-new&pivots=programming-language-python#retrieve-key-and-endpoint).

4. In a terminal, run:
   ```bash
   python quickstart.py YOUR_PROJECT_NAME  # Windows users may have to use `py` instead of `python`
   ```

Advanced users desiring control over virtual environment creation, dependency installation, environment variable setup,
and `pulumi` invocation see [the advanced setup instructions](#setup-for-advanced-users).


## Architecture overview

![Guarded RAG architecture](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/rag_architecture.svg)

App templates contain three families of complementary logic. For Guarded RAG you can [opt-in](#make-changes) to fully 
custom RAG logic and a fully custom frontend or utilize DR's off the shelf offerings:

- **AI logic**: Necessary to service AI requests and produce predictions and completions.
  ```
  deployment_*/  # Predictive model scoring logic, RAG completion logic (DIY RAG)
  notebooks/  # Document chunking, VDB creation logic (DIY RAG)
  ```
- **App Logic**: Necessary for user consumption; whether via a hosted front-end or integrating into an external consumption layer.
  ```
  frontend/  # Streamlit frontend (DIY frontend)
  docsassist/  # App business logic & runtime helpers (DIY front-end)
  ```
- **Operational Logic**: Necessary to activate DataRobot assets.
  ```
  __main__.py  # Pulumi program for configuring DataRobot to serve and monitor AI and App logic
  infra/  # Settings for resources and assets created in DataRobot
  ```

## Why build AI Apps with DataRobot app templates?

App Templates transform your AI projects from notebooks to production-ready applications. Too often, getting models into production means rewriting code, juggling credentials, and coordinating with multiple tools & teams just to make simple changes. DataRobot's composable AI apps framework eliminates these bottlenecks, letting you spend more time experimenting with your ML and app logic and less time wrestling with plumbing and deployment.

- Start building in minutes: Deploy complete AI applications instantly, then customize the AI logic or the front-end independently (no architectural rewrites needed).
- Keep working your way: Data scientists keep working in notebooks, developers in IDEs, and configs stay isolated. Update any piece without breaking others.
- Iterate with confidence: Make changes locally and deploy with confidence. Spend less time writing and troubleshooting plumbing and more time improving your app.

Each template provides an end-to-end AI architecture, from raw inputs to deployed application, while remaining highly customizable for specific business requirements.

## Make changes

### Change the RAG documents

1. Replace `assets/datarobot_english_documentation_docsassist.zip` with a new zip file containing .pdf, .docx,
   .md, or .txt documents ([example alternative docs here](https://s3.amazonaws.com/datarobot_public_datasets/ai_accelerators/acme_corp_company_policies_source_business_victoria_templates.zip)).
3. Update the `rag_documents` setting in `infra/settings_main.py` to specify the local path to the
   new zip file.
4. Run `pulumi up` to update your stack.
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   pulumi up
   ```

### Change the LLM

1. Modify your `.env`.
   ```bash
   GOOGLE_SERVICE_ACCOUNT=''  # insert json service key between the single quotes, newlines are OK
   GOOGLE_REGION=...  # default is 'us-west1'
   ```
2. Update your environment and install `google-auth`.
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   pip install google-auth
   ```
3. Update the credential type to be provisioned in `infra/settings_llm_credential.py`.
   ```python
   # credential = AzureOpenAICredentials()
   # credential.test()
   from docsassist.credentials import GoogleLLMCredentials
   credential = GoogleLLMCredentials()
   credential.test('gemini-1.5-flash-001')  # select a model for validating the credential
   ```
4. Configure a Gemini blueprint to be provisioned in `infra/settings_rag.py`.
   ```python
   # llm_id=GlobalLLM.AZURE_OPENAI_GPT_3_5_TURBO,
   llm_id=GlobalLLM.GOOGLE_GEMINI_1_5_FLASH,
   ```
5. Run `pulumi up` to update your stack.
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   pulumi up
   ```
   
### Fully custom front-end

1. Edit `infra/settings_main.py` and update `application_type` to `ApplicationType.DIY`
   - Optionally, update `APP_LOCALE` in `docsassist/i18n.py` to toggle the language.
     Supported locales are Japanese and English, with English set as the default.
2. Run `pulumi up` to update your stack with the example custom Streamlit frontend:
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   pulumi up
   ```
3. After provisioning the stack at least once, you can also edit and test the Streamlit
   front-end locally using `streamlit run app.py` from the `frontend/` directory (don't
   forget to initialize your environment using `set_env`).
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   cd frontend
   streamlit run app.py
   ```
   

### Fully custom RAG chunking, vectorization, and retrieval
1. Install additional requirements (e.g. FAISS, HuggingFace).
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   pip install -r requirements-extra.txt
   ```
2. Edit `infra/settings_main.py` and update `rag_type` to `RAGType.DIY`.
3. Run `pulumi up` to update your stack with the example custom RAG logic.
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   pulumi up
   ```
4. Edit `notebooks/build_rag.ipynb` to customize the doc chunking, vectorization logic.
5. Edit `deployment_diy_rag/custom.py` to customize the retrieval logic & LLM call.
6. Run `pulumi up` to update your stack.
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   pulumi up
   ```
## Share results

1. Log into the DataRobot application.
2. Navigate to **Registry > Applications**.
3. Navigate to the application you want to share, open the actions menu, and select **Share** from the dropdown.

## Delete all provisioned resources
```bash
pulumi down
```

## Setup for advanced users
For manual control over the setup process adapt the following steps for MacOS/Linux to your environent:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
source set_env.sh
pulumi stack init YOUR_PROJECT_NAME
pulumi up 
```
e.g. for Windows/conda/cmd.exe this would be:
```bash
conda create --prefix .venv pip
conda activate .\.venv
pip install -r requirements.txt
set_env.bat
pulumi stack init YOUR_PROJECT_NAME
pulumi up 
```
For projects that will be maintained, DataRobot recommends forking the repo so upstream fixes and improvements can be merged in the future.

## Data Privacy
Your data privacy is important to us. Data handling is governed by the DataRobot [Privacy Policy](https://www.datarobot.com/privacy/), please review before using your own data with DataRobot.
