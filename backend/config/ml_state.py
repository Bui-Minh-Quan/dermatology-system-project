# config/ml_state.py

class MLModelContainer:
    """
    A global container to hold the instantiated PyTorch models and tokenizer.
    This allows different parts of the FastAPI app to access the models in GPU memory 
    without causing circular imports.
    """
    def __init__(self):
        self.gatekeeper = None
        self.trimodal_classifier = None
        self.tokenizer = None
        self.device = None

# Instantiate a single global state object to be imported across the app
ml_state = MLModelContainer()