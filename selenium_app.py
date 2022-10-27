from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
import selenium.common.exceptions as selenium_exception
import time
import datetime
import subprocess
import locale
import os
from os.path import join, dirname
from logging_file import logger
from dotenv import load_dotenv

# .env config
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

'''
handle ping host inacessivel
verificar logica no final do loop
'''

# get the variables values of .env file
env_config = os.environ.get('MAIN_PAGE')


# set the location to pt_BR for datetime gets the corret parameters
locale.setlocale(locale.LC_TIME, 'pt_BR')


if  not env_config or len(env_config) == 0:
    logger.error(f'.env file is not set corretly or does not exists!')
    exit()

# set the main page
MAIN_PAGE = env_config

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--allow-running-insecure-content')
options.add_argument('--window-size=1920,1080')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--disable-extensions')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')
options.add_argument('--proxy-bypass-list=*')
options.add_argument("--proxy-server='direct://'")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# global function
AUTHENT = False
MAIN_BTN_XPATH = '/html/body/table/tbody/tr[1]/td/table[1]/tbody/tr[1]/td[6]'
TIME2SLEEP = 30


def goto(current_page_title, btn_xpath):
    '''this functions take the current_page and the button xpath
    so find the button and click then wait until the url has changed
    '''
    driver.find_element(By.XPATH, btn_xpath).click()
    # if the title is the MAIN PAGE, then returns
    if driver.title == 'Jobs - CUPS 1.6.3':
        return
    # this loop is really necessary ?
    logger.debug(f'CURRENT TITLE: {current_page_title} - DRIVER TITLE: {driver.title}')
    while driver.title == current_page_title:
        logger.info('Sleeping until the GOTO page is loading...')
        time.sleep(1)


def ping_printer(hostname, printer_name):
    '''run the ping command on the console
    returns false if expection was throwed
    obs: this will print the output of the command of console
    if this is no need, use subprocess.call()
    '''
    global driver
    
    try:
        subprocess.check_call(['ping', hostname], universal_newlines=True)
        logger.info('Ping sucessed. The host is ONLINE.')
        aux_timer = time.time()
        while not printer_name in driver.title and time.time() - aux_timer < 10:
            time.sleep(1)
            logger.debug(f'ping_printer(function): sleeping until returns to printers page')
        return True
    except subprocess.CalledProcessError as error:
        logger.error(f'Hostname:{hostname} - Ping error: {error}')
        aux_timer = time.time()
        while not printer_name in driver.title and time.time() - aux_timer < 10:
            time.sleep(1)
            logger.debug(f'ping_printer(function): sleeping until returns to printers page')
        return False
    
    
def release_jobs(printer_name):
    '''check if there is active jobs then:
    click on release jobs button and waits to return to the original page
    if the number of jobs dont change, something is wrong, 
    then the jobs will be CANCELED (with the proper funciton: cancel_printer_jobs())

    * it is needed to add return True or False ??
    '''

    global driver
    logger.debug(f'PRINTER NAME IN TITLE: {printer_name in driver.title}, \n{printer_name} - {driver.title}')
    # esse sleep aqui ???
    #time.sleep(5)
    if printer_name in driver.title:
        jobs_num = ''
        old_jobs_num = 0
        # variable to control the loop
        fail = False
        
        while not fail:
            try:
                # try to find the jobs number 
                jobs_num = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/p').text
                if jobs_num == 'No jobs.':
                    break
                
                # get the jobs number and compare to the old - if is the same, then the release option is going wrong
                jobs_num = int(jobs_num.split()[1])
                if jobs_num == old_jobs_num:
                    logger.error(f'(Printer: {printer_name}): Release not sucessed, something is wrong.\nAll jobs will be canceled')
                    # if there is something wrong, then canceled all jobs
                    cancel_printer_jobs(printer_name)
                    fail = True

                # jobs number will influe the XPATH, if it greather than 1, the form[x] is used. otherwise, form is used    
                if jobs_num > 1:
                    try:
                        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table[2]/tbody/tr[1]/td[7]/form[1]/input[5]').click()
                    except:
                        logger.error('Release button NOT FOUND, exiting the fuction')
                        fail = True
                else:
                    try:
                        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table[2]/tbody/tr[1]/td[7]/form/input[5]').click()
                    except:
                        logger.error('Release button NOT FOUND, exiting the fuction')
                        fail = True
                # the loop waits for the process exit and back to the printer page to continue
                logger.info('Sleeping until returns to the printers page')
                aux_timer = time.time()
                while printer_name not in driver.title and time.time() - aux_timer < 10:
                    time.sleep(1)
                    logger.debug('Sleeping...')
                if time.time() - aux_timer >= 10: logger.warning('Release jobs fail for some reason...')
                old_jobs_num = jobs_num
            except:
                logger.info('Jobs number label not found.')
                return 


def cancel_printer_jobs(printer_name):
    '''find the selection by XPATH then select
    the purge-jobs(cancel jobs) to cancel all jobs of printer
    '''
    global driver

    logger.warning(f'(Printer: {printer_name}): Cancelling all jobs!')    
    select_elem = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div[1]/form[1]/select')
    select_obj = Select(select_elem)
    select_obj.select_by_value('purge-jobs')
    

def modify_url_printer(url):
    '''this function will do:
    - find selection on the page and then select it
    - call the check_authn() to make sure that is alreasy authenticated
        - if was not, then return false and nothing happens
    - select radio buttun 'Windows Printer via SAMBA
    - modify printer url, recieve as parameter
    - returns
    '''
    
    # global variable driver (browser)
    global driver

    current_url = driver.current_url
    logger.debug(f'current_url: {current_url}, title: {driver.title}')

    # find the selection element - modify-printer
    select_elem = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div[1]/form[2]/select')
    select_obj = Select(select_elem)
    select_obj.select_by_value('modify-printer')
    
    # if was not authn, returns false so the script can redo some the previous steps 
    if not check_authn():
        return False
    
    if driver.title == 'Modify Printer - CUPS 1.6.3':
        # find radio button
        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div/form/table/tbody/tr[5]/td/input[8]').click()
        # find continue button for validate the selection
        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div/form/table/tbody/tr[6]/td[2]/input').click()
        continue_btn = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div/form/table/tbody/tr[1]/td/input')

        new_url = url + continue_btn.get_attribute('value').split('//')[1]
        logger.debug(f'New URL: {new_url}')

        continue_btn.clear()
        continue_btn.send_keys(new_url)

        # find continue button and click
        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div/form/table/tbody/tr[3]/td[2]/input').click()
        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div/form/table/tbody/tr[6]/td[2]/input').click()
        # find modify printer button and click
        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div/form/table/tbody/tr[8]/td[2]/input').click()
        
        # while driver.current_url != remove_auth(current_url):
        #     time.sleep(1)
        logger.debug('URL changed with SUCESS')

    return True
    
    
def remove_auth(string: str):
    '''remove the authentication keys: user:pass@
    from url, to make comparations more simple
    '''
    logger.debug('FUNCTION: Removing auth')
    if '@'  in string:
        string = string.split('@')
        logger.debug('REMOVE AUTH.\nnew URL (returned): https://' + string[1])
        return 'https://' + string[1]
    return string


def check_authn():
    '''check if the global var AUTHENT is true:
    if it is: returns True indicating that alredy is authenticated
    if it is not: change the url to credencials and authenticate. then go to MAINPAGE (JOBS)
    returns False indicating that was not authenticated yet
    '''

    global AUTHENT

    logger.debug(f'PAGE_TITLE:{driver.title} - URL:{driver.current_url}')
    if (not(len(driver.title) > 1) or driver.title == 'Unauthorized - CUPS v1.6.3') and not AUTHENT:
        logger.debug('Authentication in process...')
        url = driver.current_url
        url = url.split('//')
        logger.debug(f'URL: {url}')
        url[1] = 'root:redhat@' + url[1]
        url = '//'.join(url)
        AUTHENT = True
        driver.get(url)

        # find the button JOBS and click. Now the scripts are AUTHeNTICATED, i can use driver.get(url) anymore
        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table[1]/tbody/tr[1]/td[6]').click()
        return False
    return True

    
def main():
    global AUTHENT
    AUTHENT = False
    driver.get(MAIN_PAGE)
    try:
        current_time = time.time() 
        while True:

            if time.time() - current_time < TIME2SLEEP:
                continue

            # debug propurse
            logger.info(f'Time passed - WORKS IN ON!\nPage title: {driver.title}\n')
            logger.debug('The page it will refresh.')
            driver.refresh()
            # refresh the timer
            current_time = time.time()

            if driver.title == 'Erro de privacidade':
                driver.find_element(By.ID, 'details-button').click()
                driver.find_element(By.ID, 'proceed-link').click()

            # check for authentication
            check_authn()

            if remove_auth(driver.current_url) == MAIN_PAGE:
                print('---------------------------------------------------')
                
                printer = {}
                # get the number of current jobs stuck in the queue
                jobs_num = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/p').text
                
                # if there is no jobs, nothing happens, skip the logic
                if jobs_num == 'No jobs.':
                    logger.info(jobs_num)
                    continue
                
                jobs_num = int(jobs_num.split()[1])
                logger.info(f'number of jobs: {jobs_num}')
                #table_num = 2
                for tr in range(1, jobs_num + 1):
                    
                    # chek if exists more than one page
                    try:
                        driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/table[2]/tbody/tr/td[2]/form/input[5]').size != 0
                        table_num = 3  # this specify wich table we will serach for in the XPATH's
                    except:
                    # if exist, then the table now it is 3 not 2
                        #'/html/body/table/tbody/tr[1]/td/table[3]/tbody/tr[1]/td[1]/a'
                        table_num = 2
                        
                    printer['name'] = driver.find_element(By.XPATH, f'/html/body/table/tbody/tr[1]/td/table[{table_num}]/tbody/tr[{tr}]/td[1]').text
                    printer['href'] = driver.find_element(By.XPATH, f'/html/body/table/tbody/tr[1]/td/table[{table_num}]/tbody/tr[{tr}]/td[1]/a').get_attribute('href')
                    printer['state'] = driver.find_element(By.XPATH, f'/html/body/table/tbody/tr[1]/td/table[{table_num}]/tbody/tr[{tr}]/td[6]').text
                    
                    # get the time of processing jobs in state (of the printer)
                    processing_time = printer['state'].split('\n')[1]
                    processing_time = processing_time.split(' ')[:-2]
                    processing_time = ' '.join(processing_time)
                    # convert the string extract in datetime obj
                    dt = datetime.datetime.strptime(processing_time, '%a %d %b %Y %H:%M:%S')
                    # get the current time - job processing time
                    time_calc = datetime.datetime.now() - dt
                    # if the time_calc is lass than 2min, then the jobs maybe is not stuck, so we need to skip the script process
                    if not time_calc.seconds  > 120:
                        logger.info('Processing time is less than 2min. Skiping the script...')
                        continue
                    
                    # go to printer page
                    goto(driver.title, f'/html/body/table/tbody/tr[1]/td/table[2]/tbody/tr[{tr}]/td[1]/a')

                    # get the printer location
                    printer['location'] = driver.find_element(By.XPATH, f'/html/body/table/tbody/tr[1]/td/div[1]/table/tbody/tr[2]/td').text
                    logger.debug('PRINTER_LOCATION: {}'.format(printer['location']))    
                    
                    # get the hostname of the printer
                    printer['hostname'] = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div[1]/table/tbody/tr[4]/td').text.split('/')[2]
                    # based on domain and the printer location, change the url settings
                    if 'saude.df.gov.br' in printer['hostname'] and 'UPA' not in printer['location']:
                        printer['url_set'] = r'smb://saude\user_print:trakcare@'
                    else:
                        printer['url_set'] = r'smb://ihb.local\user_print:trakcare@'
                    logger.info(printer['hostname'])


                    printer_name_regex = '' # variable to get the name of the printer formatted by a specific way
                    # ensure that current page is the main page printer
                    if driver.title != 'Jobs - CUPS 1.6.3' and driver.title != 'Modify Printer - CUPS 1.6.3':
                        logger.debug('The current page is the MAIN page printer')
                        
                        # create a regex for exclude the numbers of printers name
                        regex = re.compile(r'(\w+)(-\w+)?-(\w+)')
                        printer_name_regex = regex.search(printer['name'])
                        # if printer group is not none, we have to concatenate the name
                        if printer_name_regex.group(2) is None:
                            printer_name_regex = printer_name_regex.group(1)
                        else:
                            printer_name_regex = printer_name_regex.group(1) + printer_name_regex.group(2)
                   
                   
                    # call modify_url_printer to make the proper change
                    modified = modify_url_printer(printer['url_set'])
                    logger.info('Url modifed with sucess') if modified  else logger.info('Url modifed FAIL')
                    
                    ping_status = True
                    if modified: ping_status = ping_printer(printer['hostname'], printer_name_regex)
                            
                    logger.debug('regex: {} -  printername:{}\n'.format(printer_name_regex, printer['name']))
                    logger.debug(f'modified: {modified} - ping_status: {ping_status} - printers_name in title: {printer_name_regex in driver.title}')
                    # cehck if the printer pc is offline, if it is, cancell all jobs
                    if not ping_status and modified and printer_name_regex in driver.title:
                        logger.debug('Cancel all jobs if Statment')
                        # if ping faild and url was modiefied, then cancell all jobs
                        cancel_printer_jobs(printer['name'])
                        logger.warning('{}: all jobs cancelled.'.format(printer['name']))
                    # if the pc in on, url has modiefed and the current page is the main page printer, then try to release jobs
                    elif ping_status and modified and printer_name_regex in driver.title:
                        release_jobs(printer_name_regex)
                    elif not ping_status:
                        # auxliar timer
                        aux_timer = time.time()
                        # while is not in printers page and the timer not exceded 10s, waint for the browser
                        while (printer_name_regex not in driver.title) and (time.time() - aux_timer < 10):
                            time.sleep(1)
                            logger.info('Ping FAIL. Waiting to return to printers PAGE...')
                        try:
                            logger.warning('Trying to cancel printer {} jobs'.format(printer['name']))
                            cancel_printer_jobs(printer['name'])
                        except:
                            logger.error('Something goes MUCH WRONG. SKINPING THIS STEP')
                            pass
                                                

                    logger.debug('Returning to MAIN...')
                    logger.debug(f'CURRENT TITLE: {driver.title} !!!')
                    goto(driver.title, MAIN_BTN_XPATH)

                    # THIS LOGIC IS NECESSARY ???
                    # get the number of current jobs stuck in the queue
                    jobs_num = driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/p').text
                    # if there is no jobs, nothing happens, skip the logic
                    if jobs_num == 'No jobs.':
                        break
                    jobs_num = int(jobs_num.split()[1])
                    # if the table is greather than number of jobs, quit the loop
                    if tr > jobs_num:
                        break
                
            # refresh the timer
            current_time = time.time()               

                
    except KeyboardInterrupt as e:
        logger.info('The program finshed by USER.\nDONE.')
        driver.quit()
    except selenium_exception.NoSuchElementException as e:
        logger.critical('\n------------------------------\nSomething went wrong with SELENIUM.\nRestarting the programming...\n------------------------------\n')
        logger.info(f'SELENIUM ERROR: {e}\n')
        main()
    except Exception as e:
        logger.critical(f'\n------------------------------\nUnexpected error!.\n------------------------------\n')
        logger.info(f'Error: {e}\n')
        main()
main()