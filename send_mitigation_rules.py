import requests



def simple_uploader():
    test_file = open("mitigation_rules.yaml", "rb")


    receiver_url = "http://httpbin.org/post"

    test_response = requests.post(receiver_url, files = {"form_field_name": test_file})

    if test_response.ok:
        print("Upload completed successfully!")
        print(test_response.text)
    else:
        print("Something went wrong!")


if __name__ == '__main__':
    simple_uploader()