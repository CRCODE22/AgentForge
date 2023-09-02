import importlib
import json
import os
import pathlib


class Config:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.environ.get("AGENTFORGE_CONFIG_PATH", ".agentforge")
        self.config = {}
        self.persona = {}
        self.actions = {}
        self.agents = {}
        self.tools = {}
        self.load()

    def chromadb(self):
        db_path = self.get('ChromaDB', 'persist_directory', default=None)
        db_embed = self.get('ChromaDB', 'embedding', default=None)
        return db_path, db_embed

    def get(self, section, key, default=None):
        if self.config is None:
            self.load()

        return self.config.get(section, {}).get(key, default)

    def get_config_element(self, case):
        switch = {
            "Persona": self.persona,
            "Tools": self.tools,
            "Actions": self.actions
        }
        return switch.get(case, "Invalid case")

    def get_file_path(self, file_name):
        return pathlib.Path(self.config_path) / file_name

    def get_llm(self, api, agent_name):
        model_name = self.agents[agent_name].get('Model', self.persona['Defaults']['Model'])
        model_name = self.config['ModelLibrary'].get(model_name)

        models = {
            "claude_api": {
                "module": "anthropic",
                "class": "Claude",
                "args": [model_name],
            },
            "oobabooga_api": {
                "module": "oobabooga",
                "class": "Oobabooga",
            },
            "oobabooga_v2_api": {
                "module": "oobabooga",
                "class": "OobaboogaV2",
            },
            "openai_api": {
                "module": "openai",
                "class": "GPT",
                "args": [model_name],
            },
        }

        model = models.get(api)
        if not model:
            raise ValueError(f"Unsupported Language Model API library: {api}")

        module_name = model["module"]
        module = importlib.import_module(f".llm.{module_name}", package=__package__)
        class_name = model["class"]
        model_class = getattr(module, class_name)
        args = model.get("args", [])
        return model_class(*args)

    def get_json_data(self, file_name):
        file_path = self.get_file_path(file_name)
        try:
            with open(file_path, 'r') as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            print(f"File {file_path} not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {file_path}")
            return {}

    def load(self):
        self.load_config()
        self.load_persona()
        self.load_agents()
        self.load_actions()
        self.load_tools()

    def load_actions(self):
        self.actions = self.get_json_data("actions.json")

    def load_agents(self):
        self.agents = self.get_json_data("agents.json")

    def load_config(self):
        self.config = self.get_json_data("config.json")

    def load_persona(self):
        persona_name = self.config.get('Persona', {}).get('selected', "")
        self.persona = self.get_json_data(f"personas/{persona_name}.json")

    def load_tools(self):
        self.tools = self.get_json_data("tools.json")

    def storage_api(self):
        return self.get('StorageAPI', 'selected')
