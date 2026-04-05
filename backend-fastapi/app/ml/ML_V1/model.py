import time

class Model:
    def __init__(self):
        print("Loading model...")
        time.sleep(2) # load

    def predict(self, x):
        time.sleep(0.5)  # inferência
        return {"result": x * 2}

model = Model()
