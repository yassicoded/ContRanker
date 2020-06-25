import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm_notebook as tqdm



def permit_description_scraper(permit_codes):
    """

    :param permit_codes: for a limited number of permits, we can gather more data from ladbsservices2.lacity.org
    :return: a df containing inspection table data of the link and a df containing  permit table data of the link
    """
    permit_status_data = []
    inspection_request_data = []
    full_descriptions = []
    i = 1
    with tqdm(total=len(permit_codes)) as pbar:
        for permit_code in permit_codes:
            pbar.update(1)
            # print('reading '+str(i)+' / '+str(len(permit_codes)))
            code_parts = permit_code.split('-')
            id1 = code_parts[0]
            id2 = code_parts[1]
            id3 = code_parts[2]

            URL = 'https://www.ladbsservices2.lacity.org/OnlineServices/PermitReport/PcisPermitDetail?id1=' + id1 + '&id2=' + id2 + '&id3=' + id3
            try:
                page = requests.get(URL)
                soup = BeautifulSoup(page.content, 'html.parser')

                tables = soup.find_all('table', attrs={'class': 'table table-details'})

                # dds = soup.find('dl', attrs={'class':'dl-horizontal xs-datalist'})
                # ddss = dds.find_all('dd')
                # full_descriptions.append([permit_code,ddss[6].text.strip()])

                permit_status_history = tables[0]
                table_body_1 = permit_status_history.find('tbody')
                rows = table_body_1.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    permit_req = [permit_code]
                    permit_req += [ele for ele in cols if ele]
                    permit_status_data.append(permit_req)  # Get rid of empty values

                inspection_request_history = tables[-1]
                table_body_2 = inspection_request_history.find('tbody')
                rows = table_body_2.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    cols = [ele.text.strip() for ele in cols]
                    insp_req = [permit_code]
                    insp_req += [ele for ele in cols if ele]
                    inspection_request_data.append(insp_req)  # Get rid of empty values
            except requests.exceptions.HTTPError as errh:
                print("Http Error:", errh)
            except requests.exceptions.ConnectionError as errc:
                print("Error Connecting:", errc)
            except requests.exceptions.Timeout as errt:
                print("Timeout Error:", errt)
            except requests.exceptions.RequestException as err:
                print("OOps: Something Else", err)

    inspection_requests_df = pd.DataFrame(inspection_request_data,
                                          columns=['permit_ID', 'section', 'date', 'status', 'inspector'])
    permit_statuses_df = pd.DataFrame(permit_status_data, columns=['permit_ID', 'action', 'date', 'person'])
    # full_descriptions_df = pd.DataFrame(full_descriptions,columns=['permit_ID','full_description'] )
    return inspection_requests_df, permit_statuses_df



'''
for i in range(0,2):
    permit_codes = nonadu_permits_contradu['PCIS Permit #'].unique()[i*5000:(i+1)*5000,]
    inspection_requests, permit_statuses = full_scraper(permit_codes)
    inspection_requests.to_csv('inspection_requests_contradu_'+str(i)+'.csv')
    permit_statuses.to_csv('permit_statuses_contradu_'+str(i)+'.csv')
    #full_descriptions.to_csv('full_descriptions_'+str(i)+'.csv')

'''
