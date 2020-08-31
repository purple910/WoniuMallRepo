from ronglian_sms_sdk import SmsSDK

accId = '8aaf0708732220a6017433b594b3741a'
accToken = 'bef2b9290a934cecb99bf9d55a5c2759'
appId = '8aaf0708732220a6017433b595ac7421'


def send_message(moblie, code):
    sdk = SmsSDK(accId, accToken, appId)
    tid = '1'  # 您的验证码为{1}，请于{2}内正确输入，如非本人操作，请忽略此短信。
    # mobile = '13198251538,17381560895'
    datas = (str(code), '60s')
    resp = sdk.sendMessage(tid, moblie, datas)
    resp = eval(resp)
    if resp.get('statusCode') == '000000':
        return True
    else:
        return False
    # print(resp)


if __name__ == '__main__':
    mobile = '17381560895'
    code = 5418
    b = send_message(mobile, code)
    print(b)
