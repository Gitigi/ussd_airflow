from celery import current_app as app
import requests
from structlog import get_logger
from celery.exceptions import MaxRetriesExceededError


@app.task(bind=True)
def http_task(self, request_conf):
    requests.request(**request_conf)


@app.task(bind=True)
def report_session(self, session_id, screen_content):
    # to avoid circular import
    from ussd.core import ussd_session, UssdHandlerAbstract

    logger = get_logger(__name__).bind(
        action="report_session_task", session_id=session_id
    )

    logger.info('start')

    ussd_report_session_data = screen_content['ussd_report_session']

    session = ussd_session(session_id)

    if session.get('posted'):
        logger.info("session_already_reported", posted=session['posted'])
        return

    request_conf = UssdHandlerAbstract.render_request_conf(
        session,
        ussd_report_session_data['request_conf']
    )

    if not session.get('posted'):
        response = UssdHandlerAbstract.make_request(
            http_request_conf=request_conf,
            response_session_key_save=ussd_report_session_data['session_key'],
            session=session,
            logger=logger
        )

        # check if it is the desired effect
        if response.status_code in \
                ussd_report_session_data['valid_status_code']:
            session['posted'] = True
            session.save()
            print("mwas")
        else:
            if ussd_report_session_data.get('retry_mechanism'):
                try:
                    self.retry(**screen_content[
                        'ussd_report_session']['retry_mechanism'])
                except MaxRetriesExceededError as e:
                    logger.warning("report_session_error",
                                   error_message=str(e))
    else:
        logger.info('already_reported')
