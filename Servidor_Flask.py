from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "¡Servidor activo!"

if __name__ == '__main__':
    app.run(port=5000)