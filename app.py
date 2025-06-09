from flask import Flask

app = Flask(__name__)

# This part can be used to expose endpoints to get access to the data

if __name__ == '__main__':
    app.run(debug=True)
