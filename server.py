from flask import Flask
from copy import deepcopy
from src.appConfig import loadAppConfig
from src.blueprints.demandForecastDashApi import demandForecastDashApiController
from src.blueprints.scheduleCompDashApi import schduleCompDashApiController
from src.blueprints.stateDcCompDashApi import stateDcCompDashApiController
from src.blueprints.reForecastCompDashApi import reForecastCompDashApiController
from src.blueprints.stateDeficitCompDashApi import stateDeficitCompDashApiController

appConfig = loadAppConfig()

app = Flask(__name__)
app.config['SECRET_KEY'] = appConfig.flaskSecret  # Required for the debug toolbar
app.config['DEBUG_TB_ENABLED'] = True  # Enable the toolbar
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False  # Disable redirect interception
app.config['DEBUG_TB_PROFILER_ENABLED'] = True  # Enable the profiler panel
app.config['DEBUG_TB_TEMPLATE_EDITOR_ENABLED'] = True  # Enable template editor




app.register_blueprint(demandForecastDashApiController)
app.register_blueprint(schduleCompDashApiController)
app.register_blueprint(stateDcCompDashApiController)
app.register_blueprint(stateDeficitCompDashApiController)
app.register_blueprint(reForecastCompDashApiController)


app.run(host=appConfig.flaskHost, port=appConfig.flaskPort, debug=True, use_reloader=True)

