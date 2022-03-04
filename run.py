from app import app
import logger
import views

if __name__=='__main__':
    logger.setup_gps()
    logger.start_logger()
    app.run(debug=False, host='0.0.0.0', port=5006)
