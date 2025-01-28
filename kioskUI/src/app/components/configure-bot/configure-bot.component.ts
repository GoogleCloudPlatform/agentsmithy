import { Component, inject } from '@angular/core';
import { Validators, FormBuilder, FormArray, FormGroup, AbstractControl } from '@angular/forms';
import { Router } from '@angular/router';
import { ThemeService } from '../../services/theme.service';
import { MatDialog } from '@angular/material/dialog';
import { CodeDialogComponent } from '../code-dialog/code-dialog.component';

@Component({
  selector: 'app-configure-bot',
  templateUrl: './configure-bot.component.html',
  styleUrl: './configure-bot.component.scss'
})
export class ConfigureBotComponent {
  formGroup: FormGroup;
  selectedRuntime: string = 'resoningEngine';
  selectedFramework: string = 'langchain';
  selectedTools: string = 'api';
  selectedModel: string = 'gemini';

  dialog = inject(MatDialog);

  openDialog(codeExample: any) {
    this.dialog.open(CodeDialogComponent, {
      data: {
        code: codeExample,
      },
    });
  }


  constructor(private _formBuilder: FormBuilder, private router: Router, private fb: FormBuilder, private themeService: ThemeService) { 
    this.formGroup = this.fb.group({
      formArray: this.fb.array([
        this.fb.group({
          agentName: [''],
          description: [''],
          agentType: [''],
          industry: ['']
        }),
        this.fb.group({ /* runtime controls */ }),
        this.fb.group({ /* other controls */ })
      ])
    });
  }

  get formArray(): AbstractControl | null { return this.formGroup.get('formArray'); }

  stepperConfig = [
    {
      heading: 'Agent Properties',
      stepHeading: 'Properties',
      contentType: 'form',
      fields: [
        { label: 'Agent Name', type: 'input', controlName: 'agentName', placeholder: '', required: true },
        { label: 'Description', type: 'input', controlName: 'description', placeholder: '', required: true },
        { label: 'Agent Type', type: 'select', controlName: 'agentType', options: [
          { value: 'option1', label: 'Option 1' },
          { value: 'option2', label: 'Option 2', disabled: true },
          { value: 'option3', label: 'Option 3' }
        ] },
        { label: 'Industry', type: 'select', controlName: 'industry', options: [
          { value: 'option1', label: 'Option 1' },
          { value: 'option2', label: 'Option 2', disabled: true },
          { value: 'option3', label: 'Option 3' }
        ] }
      ],
      hasNext: true,
      hasPrevious: false,
      hasHome: true,
      hasCode: false,
      hasBack: true
    },
    {
      heading: 'Runtime',
      stepHeading: 'Runtime',
      contentType: 'options',
      options: [
        { 
          label: 'Vertex AI Reasoning Engine', 
          isSelected: true, 
          onClick: () => this.selectRunTime('Vertex AI Reasoning Engine'), 
          subtitle: 'Vertex AI Reasoning Engine is purpose-built for deploying and serving machine learning models, offering specialized features like GPU support and model management, while Cloud Run is a more general-purpose serverless platform for deploying and scaling any containerized application. Choose Vertex AI Reasoning Engine if your focus is on machine learning model deployment and serving, and opt for Cloud Run when you need a versatile serverless platform for general-purpose applications.',
          caption: '# Initialize the Vertex AI client \naiplatform.init(project="your-project-id", location="your-region")\n\n# Deploy a model to the Vertex AI Reasoning Engine \nmodel = aiplatform.Model.upload( \n\tdisplay_name="your-model-name", \n\tartifact_uri="gs://your-bucket/your-model-path", \n\tserving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/your-\ncontainer-image", ) endpoint = model.deploy( machine_type="n1-standard-4", )'
        },
        { 
          label: 'Cloud Run', 
          isSelected: false, 
          onClick: () => this.selectRunTime('Cloud Run'),
          subtitle: 'Cloud Run is a general-purpose service for deploying and running any containerized application, including web applications, APIs, and microservices.',
          caption: 'apiVersion: serving.knative.dev/v1 \nkind: Service \nmetadata: \n\tname: your-service-name \nspec: \n\ttemplate: \n\t\tspec: \n\t\t\tcontainers: \n\t\t\t\t-image: us-docker.pkg.dev/cloudrun/container/hello \n\t\t\tports: \n\t\t\t\t-containerPort: 8080' 
        }
      ],
      selectedOptionResponse: {
        subtitle: 'Vertex AI Reasoning Engine is purpose-built for deploying and serving machine learning models, offering specialized features like GPU support and model management, while Cloud Run is a more general-purpose serverless platform for deploying and scaling any containerized application. Choose Vertex AI Reasoning Engine if your focus is on machine learning model deployment and serving, and opt for Cloud Run when you need a versatile serverless platform for general-purpose applications.',
        caption: '# Initialize the Vertex AI client \naiplatform.init(project="your-project-id", location="your-region")\n\n# Deploy a model to the Vertex AI Reasoning Engine \nmodel = aiplatform.Model.upload( \n\tdisplay_name="your-model-name", \n\tartifact_uri="gs://your-bucket/your-model-path", \n\tserving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/your-\ncontainer-image", ) endpoint = model.deploy( machine_type="n1-standard-4", )'
      },
      hasNext: true,
      hasPrevious: true,
      hasHome: true,
      hasCode: true
    },
    {
      heading: 'Orchestration Framework',
      stepHeading: 'Framework',
      contentType: 'options',
      options: [
        { 
          label: 'Langchain/Langgraph', 
          isSelected: true, 
          onClick: () => this.selectFramework('Langchain/Langgraph'), 
          subtitle: 'LangChain (with its visual counterpart LangGraph) is a framework for building applications with large language models (LLMs). It provides tools to chain together LLMs with other components, like prompts and external data sources, to create complex applications.',
          caption: 'from langchain.llms import Gemini \nfrom langchain.prompts import PromptTemplate \n\nllm = Gemini(model="gemini-pro", temperature=0.9) # Using Gemini Pro \nprompt = PromptTemplate( \n\tinput_variables=["product"], \n\ttemplate="What is a good name for a company that makes {product}?", \n) \nprint(llm(prompt.format(product="colorful socks")))'
        },
        { 
          label: 'LlamaIndex', 
          isSelected: false, 
          onClick: () => this.selectFramework('LlamaIndex'),
          subtitle: 'LlamaIndex (formerly GPT Index) is a data framework that helps you connect your external data to large language models (LLMs). It provides tools for structuring, indexing, and querying your data sources, allowing LLMs to access and utilize this information effectively.',
          caption: 'from llama_index import SimpleDirectoryReader, GPTListIndex, LLMPredictor, \nServiceContext \nfrom langchain.llms import Gemini \n\ndocuments = SimpleDirectoryReader(\'data\').load_data() \nindex = GPTListIndex.from_documents(documents) \n\n# Define LLM and service context using Gemini \nllm_predictor = LLMPredictor(llm=Gemini(model="gemini-pro", temperature=0)) \nservice_context = ServiceContext.from_defaults(llm_predictor=llm_predictor) \nquery_engine = index.as_query_engine(service_context=service_context) \nresponse = query_engine.query("What is the main topic?") \nprint(response)' 
        },
        { 
          label: 'Vertex Agent Framework', 
          isSelected: false, 
          onClick: () => this.selectFramework('Vertex Agent Framework'),
          subtitle: 'The Vertex AI Agent Framework is a new tool (currently in preview) that allows developers to build and deploy agents that use LLMs to connect with APIs, data, and other applications. It simplifies the creation of agents that can automate tasks, retrieve information, and interact with the world.',
          caption: 'from google.cloud import aiplatform \n\n# Initialize the Vertex AI client \naiplatform.init(project="your-project-id", location="your-region") \n\n# Create an agent \nagent = aiplatform.Agent.create( \ndisplay_name="my-agent", llm_model="text-bison@001", tools=[aiplatform.Tool.from_python_package( \ndisplay_name="wikipedia", python_package_uri="gs://my-bucket/wikipedia.tar.gz", )] )' 
        }
      ],
      selectedOptionResponse: {
        subtitle: 'LangChain (with its visual counterpart LangGraph) is a framework for building applications with large language models (LLMs). It provides tools to chain together LLMs with other components, like prompts and external data sources, to create complex applications.',
        caption: 'from langchain.llms import Gemini \nfrom langchain.prompts import PromptTemplate \n\nllm = Gemini(model="gemini-pro", temperature=0.9) # Using Gemini Pro \nprompt = PromptTemplate( \n\tinput_variables=["product"], \n\ttemplate="What is a good name for a company that makes {product}?", \n) \nprint(llm(prompt.format(product="colorful socks")))'
      },
      hasNext: true,
      hasPrevious: true,
      hasHome: true,
      hasCode: true
    },

    {
      heading: 'Tools',
      stepHeading: 'Tools',
      contentType: 'options',
      options: [
        { 
          label: 'API', 
          isSelected: true, 
          onClick: () => this.selectTools('API'), 
          subtitle: 'An API allows the LLM to interact with external services and retrieve information or perform actions. This expands the LLM\'s capabilities beyond just generating text, enabling it to access real-time data, interact with other applications, and perform a wider range of tasks.',
          caption: 'from langchain.agents import Tool \n\n# Define the tool (assuming \'get_weather\' function is already defined) \nweather_tool = Tool( \n\tname="Get Weather", \n\tfunc=get_weather, \n\tdescription="Get current weather for a location." \n)'
        },
        { 
          label: 'Pre-build Tool', 
          isSelected: false, 
          onClick: () => this.selectTools('Pre-build Tool'),
          subtitle: '"Pre-built" tools for LLMs are ready-made components that provide easy access to common functionalities and services, like searching the web or accessing specific APIs. These tools are pre-configured and often come bundled with platforms like LangChain, allowing developers to quickly integrate them into their applications without building everything from scratch.',
          caption: 'from langchain.agents import load_tools \n\n# Load the pre-built Google Search tool \ntools = load_tools(["google-search"]) \n\n# Use the tool (e.g., within an agent) \ntools[0].run("What\'s the weather in Boston, MA?")' 
        },
        { 
          label: 'TBD', 
          isSelected: false, 
          onClick: () => this.selectTools('TBD'),
          subtitle: 'Tempus interdum tincidunt suspendisse pulvinar. In habitant lorem quis viverra. Cum facilisi sit scelerisque mi sed porttitor mauris. Adipiscing pellentesque lobortis eget amet lectus. Nulla a et sit at id massa purus volutpat urna. Accumsan.',
          caption: 'aiplatform.init(project="your-project-id", location="your-region") \nllm = VertexAI(model_name="text-bison@001") \nagent = "Agent description here" \nremote_agent = aiplatform.reasoning_engines.ReasoningEngine.create( \n\tagent=agent, \n\trequirements=[ "google-cloud-aiplatform[langchain,reasoningengine]", \n\t"cloudpickle==3.0.0", "pydantic==2.7.4", "langchain-google-community", "google-cloud-discoveryengine", ], \n)' 
        }
      ],
      selectedOptionResponse: {
        subtitle: 'An API allows the LLM to interact with external services and retrieve information or perform actions. This expands the LLM\'s capabilities beyond just generating text, enabling it to access real-time data, interact with other applications, and perform a wider range of tasks.',
        caption: 'from langchain.agents import Tool \n\n# Define the tool (assuming \'get_weather\' function is already defined) \nweather_tool = Tool( \n\tname="Get Weather", \n\tfunc=get_weather, \n\tdescription="Get current weather for a location." \n)'
      },
      hasNext: true,
      hasPrevious: true,
      hasHome: true,
      hasCode: true
    },
    {
      heading: 'Model',
      stepHeading: 'Model',
      contentType: 'options',
      options: [
        { 
          label: 'Gemini', 
          isSelected: true, 
          onClick: () => this.selectModel('Gemini'), 
          subtitle: 'Gemini is a family of large language models (LLMs) from Google AI, capable of text generation, code generation, translation, and question answering.',
          caption: 'from langchain.llms import Gemini \n\nllm = Gemini(model="gemini-pro") \nresponse = llm("Tell me a joke.") \nprint(response)'
        },
        { 
          label: 'Claude (Model Garden)', 
          isSelected: false, 
          onClick: () => this.selectModel('Claude (Model Garden)'),
          subtitle: 'Claude is a large language model created by Anthropic, focused on being helpful, harmless, and honest. You can use Claude for tasks like summarizing articles or documents, engaging in natural-sounding conversations, generating different kinds of text formats, and providing informative answers to your questions.',
          caption: 'import anthropic \n\nclient = anthropic.Anthropic() \nresponse = client.completions.create( \n\tmodel="claude-2", \n\tprompt="Write a short poem about the ocean." \n) \nprint(response.completion)' 
        }
      ],
      selectedOptionResponse: {
        subtitle: 'Gemini is a family of large language models (LLMs) from Google AI, capable of text generation, code generation, translation, and question answering.',
        caption: 'from langchain.llms import Gemini \n\nllm = Gemini(model="gemini-pro") \nresponse = llm("Tell me a joke.") \nprint(response)'
      },
      hasNext: false,
      hasPrevious: true,
      hasHome: true,
      hasSubmit: true,
      hasCode: false
    }
  ];

  ngOnInit() {
    this.formGroup = this._formBuilder.group({
      formArray: this._formBuilder.array([
        this._formBuilder.group({
          agentName: ['', Validators.required],
          description: ['', Validators.required],
          agentType: ['', Validators.required],
          industry: ['', Validators.required],
        }),
        this._formBuilder.group({
          runTime: ['', Validators.required]
        }),
        this._formBuilder.group({
          framework: ['', Validators.required]
        }),
        this._formBuilder.group({
          tools: ['', Validators.required]
        }),
        this._formBuilder.group({
          model: ['', Validators.required]
        }),
      ])
    });
  }
  
  selectRunTime(value: string) {
    console.log(value);
    this.selectedRuntime = value;
  }

  selectFramework(value: string) {
    console.log(value);
    this.selectedFramework = value;
  }

  selectTools(value: string) {
    console.log(value);
    this.selectedTools = value;
  }

  selectModel(value: string) {
    console.log(value);
    this.selectedModel = value;
  }

  goToHome() {
    this.router.navigate(['/']);
  }

  onRadioChange(section: any, selectedOption: any) {
    section.options.forEach((option: { isSelected: boolean; }) => {
      option.isSelected = option === selectedOption; 
    });
    section.selectedOptionResponse = {
      subtitle : selectedOption.subtitle,
      caption: selectedOption.caption
    }
    selectedOption.onClick(); 
  }

  goToSpinnerComponent() {
    this.submitForm();
    this.router.navigate(['/spinner']);
  }

  submitForm() {
    console.log(this.formGroup.value);
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }
}
