class Account:
    def __init__(self, email, email_password, password, uid, access_token, user_agent, proxy_url):
        self.email_password = email_password
        self.email = email
        self.password = password
        self.uid = uid
        self.access_token = access_token
        self.user_agent = user_agent
        self.proxy_url = proxy_url

    def __repr__(self):
        return f"[{self.email}]"
