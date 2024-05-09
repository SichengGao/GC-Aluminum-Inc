import re
import json
import time
import traceback

from openai import OpenAI
import openai
from loguru import logger


def openai_parse_pdf(api_key='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', file_path='PO133.pdf', model='gpt-4-turbo-preview', content='Here is Place Order from a client. Find out the PO number (Place order number), Vendor name and address,and ship to (shipping address of the order). Present them to me in a dictionary format.'):
    # api_key = "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"
    openai.api_key = api_key
    client = OpenAI(api_key=api_key)
    assitant_id = 'asst_LehFlrfdvcnwhAtmqJBqV02b'

    def upload_file(filepath):
        try:
            # Open the file in binary read mode
            with open(filepath, 'rb') as file:
                # Upload the file to OpenAI's server
                response = client.files.create(
                    file=file,
                    purpose='assistants'  # or 'fine-tuning' based on your need
                )
            print(f"File uploaded. File ID: {response.id}")
            return response.id
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None

    file_id = upload_file(file_path)

    # # Upload a file with an "assistants" purpose
    # file = client.files.create(
    #   # file=open("PO133.pdf", "rb"),
    #   file=open(file_path, "rb"),
    #   purpose='assistants'
    # )
    # #  create the Assistant with the uploaded file
    # assistant = client.beta.assistants.create(
    #     name="analyzes pdf",
    #     instructions="Assistants API analyzes pdf files",
    #     tools=[{"type": "code_interpreter"}],
    #     model=model,
    #     file_ids=[file.id]
    # )
    #
    # thread = client.beta.threads.create(
    #   messages=[
    #     {
    #       "role": "user",
    #       "content": "Please extract the text of the given pdf file",
    #       "file_ids": [file_id]
    #     }
    #   ]
    # )

    try:
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": "try this one",
                    "attachments": [
                        {
                            "file_id": file_id,
                            "tools": [{"type": "file_search"}]
                        }
                ]
                }
            ]
        )
        print("Thread created successfully:", thread)
    except Exception as e:
        print(f"Error creating thread: {e}")


    # Create a Run
    run = client.beta.threads.runs.create_and_poll(
      thread_id=thread.id,
      assistant_id=assitant_id,
      # instructions="Please address the user as Jin. The user has a premium account."
    )
    logger.info(f'等待返回答案，每5秒查询一次。。。')
    while True:
        time.sleep(5)
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(
            thread_id=thread.id
            )
            logger.debug(f'openai返回数据：{messages}')
            try:
                data = messages.dict()['data'][0]['content'][0]['text']['value']
                # data = 'I have extracted the text from the PDF file. Here are the details in the requested dictionary format:\n\n```python\n{\n  "PO number": "004185",\n  "Vendor name and address": {\n    "name": "ATLAS ALLIANCES LIMITED",\n    "address": "RM 1003, 10/F., RIGHTFUL CTR., 12 TAK HING ST., TST KIN, HONG KONG,"\n  },\n  "Ship to (shipping address)": {\n    "name": "MAIN WAREHOUSE Leading Edge Distribution",\n    "address": "1333 E Highland Rd, Suite C Macedonia, OH 44056-2398"\n  }\n}\n```'
                # import pdb
                # pdb.set_trace()
                print(data + 'XXXXXXXXXXXXXXX')
                # if 'python' in data:
                #     try:
                #         data = json.loads(re.findall("python\\n.*?= (.*?)\\n```", data, re.S)[0].replace('\n', ''))
                #         print(data+'!!!!!')
                #     except:
                #         datas = re.findall("python\\n(.*?)\\n```", data, re.S)
                #         data = {}
                #         for data_ in datas:
                #             data_ = data_.replace('\n', '')
                #             data_ = json.loads(data_)
                #             if data_.get('PO_number'):
                #                 data.update(data_)
                #             else:
                #                 data['Description'] = [d['Description'] for d in data_]
                #         logger.success(f'openai答案：{data}')
                #         return data




                if 'json' in data:
                    try:
                        data = json.loads(re.findall("json\\n.*?= (.*?)\\n```", data, re.S)[0].replace('\n', ''))
                    except:
                        data = json.loads(re.findall("```json\\n(.*?)\\n```", data, re.S)[0].replace('\n', ''))
                else:
                    data = {}
                if data:
                    if 'Items' in data:
                        descriptions = [item['Description'] for item in data['Items'].values()]
                        description = '; '.join(descriptions)
                        data['description'] = description
                        data.pop('Items')
                    if 'items' in data:
                        description = '; '. join([dd['description'] for dd in data.get('items', [])])
                        data['description'] = description
                        data.pop('items')

            except:
                logger.info('OpenAI returns data exceptions')
                traceback.print_exc()
                import pdb
                pdb.set_trace()
                data = {}
            logger.success(f'openai答案：{data}')
            # openai答案：{
            # 'PO_number': '004185',
            # 'Vendor_name': 'ATLAS ALLIANCES LIMITED',
            # 'Vendor_address': 'RM 1003, 10/F., RIGHTFUL CTR., 12 TAK HING ST., TST, KIN, HONG KONG',
            # 'Ship_to': 'Leading Edge Distribution, 1333 E Highland Rd, Suite C, Macedonia, OH 44056-2398'
            # }
            if data:
                return data
            # import pdb
            # pdb.set_trace()
            # return data
        else:
            logger.info(f'openai回答状态: {run.status}')


if __name__ == '__main__':
    openai_parse_pdf()

