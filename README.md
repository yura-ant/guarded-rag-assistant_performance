# DocsAssist Recipe
DocsAssist is an easily customizable recipe for building a RAG-powered chatbot. 

In addition to creating a hosted, shareable user interface, DocsAssist provides:
* Regex and prompt-injection guardrails
* A predictive sidecar model that evaluates response quality
* GenAI-focused custom metrics that automatically refresh on a schedule
* DataRobot ML Ops hosting, monitoring, and governing the individual backend deployments


![Using DocsAssist](https://s3.amazonaws.com/datarobot_public/drx/drx_gifs/docs_assist_ui.gif)


## Getting started
1. ```
   git clone https://github.com/datarobot/recipe-docsassist.git
   ```

2. Create the file `.env` in the root directory of the repo and populate your credentials.
   ```
   DATAROBOT_API_TOKEN=...
   DATAROBOT_ENDPOINT=...  # e.g. https://app.datarobot.com/api/v2
   OPENAI_API_KEY=...
   OPENAI_API_VERSION=...  # e.g. 2024-02-01
   OPENAI_API_BASE=...  # e.g. https://your_org.openai.azure.com/
   OPENAI_API_DEPLOYMENT_ID=...  # e.g. gpt-4
   PULUMI_CONFIG_PASSPHRASE=...  # required, choose an alphanumeric passphrase to be used for encrypting pulumi config
   ```
   
3. Set environment variables using your `.env` file. We have provided a helper script
   you may use for this step
   ```
   # Exports environment variables from .env, activates virtual environment .venv/ if present
   source set_env.sh
   ```

4. Create a new stack for your project, then provision all resources.
   ```
   pulumi stack init YOUR_PROJECT_NAME
   pulumi up
   ```
   Dependencies are automatically installed in a new virtual environment located in `.venv/`.

### Details
Instructions for installing pulumi are [here][pulumi-install]. In many cases this can be done
with:
```
curl -fsSL https://get.pulumi.com | sh
pulumi login --local
```

Python must be installed for this project to run. By default, pulumi will use the python binary
aliased to `python3` to create a new virtual environment. If you wish to self-manage your virtual
environment, delete the `virtualenv` and `toolchain` keys from `Pulumi.yaml` before running `pulumi up`.


For projects that will be maintained we recommend forking the repo so upstream fixes and
improvements can be merged in the future.

[pulumi-install]: https://www.pulumi.com/docs/iac/download-install/


## Make changes
### Change the RAG documents
1. Replace `assets/datarobot_english_documentation_docsassist.zip` with a new zip file of pdf, docx,
   md, or txt documents (example alternative docs here: [AcmeCorp Corporate Policies][corp-policies]).
3. Update the `rag_documents` setting in `infra/settings_main.py` to specify the local path to the
   new zip file.
4. Run `pulumi up` to update your stack

[corp-policies]: https://s3.amazonaws.com/datarobot_public_datasets/ai_accelerators/acme_corp_company_policies_source_business_victoria_templates.zip

### Fully custom frontend
1. Edit `infra/settings_main.py` and update `application_type` to `ApplicationType.DIY`
2. Run `pulumi up` to update your stack with the example custom streamlit frontend
3. After provisioning the stack at least once, you can also edit and test the streamlit
   frontend locally using `streamlit run app.py` from the `frontend/` directory (don't 
   forget to initialize your environment using `source set_env.sh`)

### Fully custom RAG chunking, vectorization, retrieval
1. Install additional requirements (e.g. FAISS, HuggingFace)
   ```
   source set_env.sh
   pip install -r requirements-extra.txt
   ```
2. Edit `infra/settings_main.py` and update `rag_type` to `RAGType.DIY`
3. Run `pulumi up` to update your stack with the example custom RAG logic
4. - Edit `data_science/build_rag.ipynb` to customize the doc chunking, vectorization logic.
   - Edit `deployment_diy_rag/custom.py` to customize the retrieval logic
   - Run `pulumi up` to update your stack


## Delete all provisioned resources
```
pulumi down
```
