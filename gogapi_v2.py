form = """
<form action="https://secure.gog.com/login" method="post" name="login_form" autocomplete="on" id="login_form">
   <div class="lg_marker2"></div>
   <div id="login_main_container" class="lg_main">
      <div class="message_container">
         <div class="lg_msg1">
            <div id="login_main_message_container" class="lg_msg2">
               <p class="login_error" style="display:none">the email or password is incorrect. if you ever forget your password, please <span id="password_reset_go_to" class="error_un">click here</span>.</p>
               <p class="reset" >if you ever forget your user account password, please <span id="password_reset_go_to2" class="dark_un">click here</span>.</p>
            </div>
          </div>
       </div>
       <span class="lg_label">E-mail:</span>
       <input id="log_email" type="text" name="log_email" value="" autocomplete="on" class="" />
       <div class="lg_separator"></div>
       <span class="lg_label">Password:</span>
       <input id="log_password" type="password" name="log_password" value="" autocomplete="on" class=""/>
       <div class="lg_spinner hideMeOnFormChange">Please wait</div>
       <input id="redirectOk" type="hidden" name="redirectOk" value="/" />
       <div class="btn_login gog_btn green"><input id="submitForLoginForm" class="btn_login" type="submit" value="Log me in"/>Log me in</div>
    </div> 
    <input type="hidden" id="unlockSettings" name="unlockSettings" value="0" />
</form>
"""
ajax = """
$.ajax({
  url:"/user/ajax",
  data:{
    a:"get",
    c:__ctr,
    p1:e,
    p2:c,
    auth:"",
    games:_pageGamesList.join(","),
    gutm:b,
    pp:a},
  timeout:30000,
  type:"POST",
  dataType:"json",
  beforeSend:loadUserBeforeSend,
  error:loadUserError,
  success:loadUserSuccess,
  cache:false
})
"""

import requests,re

class Browser:
    def __init__(self):
        self.cookies = {}
        #self.cookies = {"guc_al":"0","sessions_gog_com":"0","__utma":"95732803.1911890316.1399672018.1399672018.1399672018.1","__utmb":"95732803.5.9.1399672201295","__utmz":"95732803.1399672018.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)"}
        self.headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Encoding":"gzip, deflate","Accept-Language":"en-us,ko;q=0.7,en;q=0.3",
"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:28.0) Gecko/20100101 Firefox/28.0",
"Referer":"http://www.gog.com"}
    def post(self,url,params={}):
        self.json = {}
        self.text = ""
        answer = requests.post(url,params=params,cookies=self.cookies,headers=self.headers)
        self.cookies.update(answer.cookies)
        try:
            self.json = answer.json()
        except:
            pass
        try:
            self.text = answer.text
        except:
            pass
    def get(self,url,params={}):
        self.json = {}
        self.text = ""
        answer = requests.get(url,params=params,cookies=self.cookies,headers=self.headers)
        self.cookies.update(answer.cookies)
        try:
            self.json = answer.json()
        except:
            pass
        try:
            self.text = answer.text
        except:
            pass

b = Browser()
b.get("https://www.gog.com/")
gutm = re.findall('<input\s+type="hidden"\s+id="gutm"\s+value="(.*?)"',b.text)[0]
ctr = "frontpage"
print "gutm:",gutm
b.post("https://www.gog.com/user/ajax",{
    "a":"get","c":ctr,"p1":False,"p2":False,"auth":"",
    "games":"","gutm":gutm,"pp":""})
ajax = b.json
print "AJAX1:",ajax
buk = ajax["buk"]
print "buk:",buk
b.post("https://secure.gog.com/login",{
    "buk":buk,
    "unlockSettings":"1",
    "log_email":"saluk64007@gmail.com",
    "log_password":"wan3bane",
    "redirectOk":"/",
    })
b.post("https://www.gog.com/user/ajax",{
    "a":"get","c":ctr,"p1":"false","p2":"false","auth":"",
    "games":"","gutm":gutm,"pp":""})
ajax = b.json
print "AJAX2:",ajax
b.get("https://secure.gog.com/account/games/shelf")
print b.cookies
print re.findall('data-gameindex="(.*?)"',b.text)
b.post("https://secure.gog.com/login",{
    "buk":buk,
    "unlockSettings":"1",
    "log_email":"saluk64007@gmail.com",
    "log_password":"wan3bane",
    "redirectOk":"/",
    })
b.post("https://www.gog.com/user/ajax",{
    "a":"get","c":ctr,"p1":"false","p2":"false","auth":"",
    "games":"","gutm":gutm,"pp":""})
ajax = b.json
print "AJAX2:",ajax
b.get("https://secure.gog.com/account/games/shelf")
print b.cookies
print re.findall('data-gameindex="(.*?)"',b.text)
f = open("gogresult2.html","w")
f.write(b.text.encode("utf8"))
f.close()
