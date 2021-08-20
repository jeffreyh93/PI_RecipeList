import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivy.uix.bubble import Bubble, BubbleButton
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from functools import partial
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.config import Config

import json
import requests
import time

API_URL = "https://good-team.herokuapp.com"

#Home Login/Pin Screen
#---------------------------------------
class VM_Home(Screen):
    pin = ObjectProperty(None)
    email = ObjectProperty(None)
    msg = ObjectProperty(None)
    userId = ObjectProperty(None)
    
    def exit_btn(self):
        exit()
    
    def on_enter(self):
        elec_id = 0
        elec_name = 0
        voter_id = 0
        vote_select = 0
        index_choice = 0
        token = 0
    
    def process_pin(self):      
        sendObj = {}
        sendObj['email'] = self.email.text
        sendObj['password'] = self.pin.text
        
        loginRes = requests.post(API_URL + "/login", json = sendObj)
        
        if loginRes.status_code == 200:
            self.manager.current = "election_list"
            resObj = json.loads(loginRes.text)
            app = App.get_running_app()
            app.voter_id = resObj["_id"]
            app.token = resObj["token"]
            
        else:
            self.msg.text = "Email/Password\nis not accepted"
            self.pin.text = ""
            
#Elections List Screen
#---------------------------------------
class VM_Election_List(Screen):
    
    # event handler election button
    def process_elec(self, *args):
        app = App.get_running_app()
        app.elec_id = args[0]
        self.ids.grid.clear_widgets()
        self.manager.current = "election_det"
    
    # event handler back button
    def backBtn(self, instance):
        self.manager.screens[0].ids.pin.text = ""
        self.manager.screens[0].ids.email.text = ""
        self.ids.grid.clear_widgets()
        self.manager.current = "election_home"
    
    # triggers when screen is entered
    def on_enter(self):
        app = App.get_running_app()
        token = app.token
        voter_id = app.voter_id
        
        titleLbl = Label(text="Eligible Elections",
                      font_size='30sp',
                      size_hint=(None,None),
                      size=(self.width, self.height/8))
        self.ids.grid.add_widget(titleLbl)
        
        # API Call: get the list of eligible elections voter can vote for
        headerObj = {"voter-token": token}
        election_list = requests.get(API_URL + "/voters/elections", headers=headerObj)
        
        if election_list.status_code == 200:
            electionsStr = election_list.json()["votable"]
            
            for i in range(len(electionsStr)):
                election_det = requests.get(API_URL + "/elections/" + electionsStr[i], headers=headerObj)
                
                if election_det.status_code == 200:
                    detail_obj = election_det.json()
                    button = Button(text="Election " + str(i) + " Name: " + detail_obj["election"]["details"],
                                size_hint=(None, None),
                                size=(self.width, self.height/4))
                    button.bind(on_press=partial(self.process_elec, electionsStr[i]))
                    self.ids.grid.add_widget(button)
        
        #below code is just to place the finish button on the far bottom right of the grid
        padLbl = Label(text="",
                       size_hint=(None,None),
                       size=(self.width, self.height/16))
        self.ids.grid.add_widget(padLbl)
        
        finishBtn = Button(text="Finish",
                           size_hint=(None,None),
                           size=(self.width/4, self.height/8))
        finishBtn.bind(on_press=self.backBtn)
        self.ids.grid.add_widget(finishBtn)
               

#Election Details Screen
#---------------------------------------
class VM_Election_Det(Screen):
    # event handler back button
    def backBtn(self, instance):
        self.ids.grid.clear_widgets()
        self.manager.current = "election_list"
    
    # event handler selection made
    def vote_confirm(self, *args):
        self.ids.grid.clear_widgets()
        app = App.get_running_app()
        app.vote_select = args[0]
        app.elec_name = args[1]
        app.index_choice = args[2]
        self.manager.current = "vote_confirm"
    
    def on_enter(self):
        app = App.get_running_app()
        
        voter_id = app.voter_id
        election_id = app.elec_id
        token = app.token
        
        headerObj = {"voter-token": token}
        
        # API Call: use the election id to grab the election details
        election_det = requests.get(API_URL + "/elections/" + election_id, headers=headerObj)
        
        count = 0
        
        if election_det.status_code == 200:
            detail_obj = election_det.json()
            
            elec_name = detail_obj["election"]["details"]
            elec_choices = detail_obj["election"]["choices"]
            titleLbl = Label(text="Election Name: " + elec_name,
                      font_size='30sp',
                      size_hint=(None,None),
                      size=(self.width, self.height/8))
            self.ids.grid.add_widget(titleLbl)
            
            for i in range(len(elec_choices)):
                option = elec_choices[i]["option"]
                
                count = i + 1
                button = Button(text="Option " + str(count) + ": " + option,
                                size_hint=(None,None),
                                size=(self.width, self.height/4))
                button.bind(on_press=partial(self.vote_confirm, option, elec_name, str(count - 1)))
                self.ids.grid.add_widget(button)
                
        #below code is just to place the finish button on the far bottom right of the grid
        padLbl = Label(text="",
                       size_hint=(None,None),
                       size=(self.width, self.height/16))
        self.ids.grid.add_widget(padLbl)
        
        finishBtn = Button(text="Back",
                           size_hint=(None,None),
                           size=(self.width/4, self.height/8))
        finishBtn.bind(on_press=self.backBtn)
        self.ids.grid.add_widget(finishBtn)   

#Vote Confirmation Screen
#---------------------------------------
class VM_Vote_Confirm(Screen):
    def adminLogin(self):
        adminObj = {}
        adminObj['email'] = "light"
        adminObj['password'] = "light"
        
        loginRes = requests.post(API_URL + "/login", json = adminObj)
        if loginRes.status_code == 200:
            resObj = json.loads(loginRes.text)
            return resObj["token"]
    
    # makes api call to cast the vote
    def confVote(self, *args):        
        voter_id = args[0]
        election_id = args[1]
        vote_select = args[2]
        index_choice = args[3]
        
        sendObj = {}
        sendObj['voter_id'] = voter_id
        sendObj['election_id'] = election_id
        sendObj['choice'] = int(index_choice)
        
        app = App.get_running_app()
        token = self.adminLogin()
        headerObj = {"voter-token": token}      
            
        vote_res = requests.post(API_URL + "/ballots", json = sendObj, headers = headerObj)
        print(vote_res.text)
        if vote_res.status_code == 200:
            popup = Popup(title='Vote Popup',
                          content=Label(text='Vote successfully placed!\nReturning to elections list screen'),
                          size_hint=(None, None),
                          size=(400,400))
            popup.open()
            Clock.schedule_once(popup.dismiss, 3)
            
            election_id = 0
            vote_select = 0
            self.ids.grid.clear_widgets()
            self.manager.current = "election_list"
        else:
            popup = Popup(title='Vote Popup',
                          content=Label(text='Error occured!\nReturning to elections list screen'),
                          size_hint=(None, None),
                          size=(400,400))
            popup.open()
            Clock.schedule_once(popup.dismiss, 3)
            
            election_id = 0
            vote_select = 0
            self.ids.grid.clear_widgets()
            self.manager.current = "election_list"
    # event handler back button
    def backBtn(self, instance):
        self.ids.grid.clear_widgets()
        self.manager.current = "election_det"
    
    def on_enter(self):
        app = App.get_running_app()
        
        voter_id = app.voter_id
        election_id = app.elec_id
        vote_select = app.vote_select
        elec_name = app.elec_name
        index_choice = app.index_choice
        
        titleLbl = Label(text="Please confirm the following information:",
                          font_size='30sp',
                          size_hint=(None,None),
                          size=(self.width, self.height/8))
        self.ids.grid.add_widget(titleLbl)            
        
        electionLbl = Label(text="Election Details",
                          font_size='20sp',
                          size_hint=(None,None),
                          size=(self.width, self.height/8))
        self.ids.grid.add_widget(electionLbl)
        
        electionLbl = Label(text="Election Name = " + elec_name,
                          font_size='15sp',
                          size_hint=(None,None),
                          size=(self.width, self.height/16))
        self.ids.grid.add_widget(electionLbl)
        
        electionLbl = Label(text="Option Choice = " + vote_select,
                          font_size='15sp',
                          size_hint=(None,None),
                          size=(self.width, self.height/16))
        self.ids.grid.add_widget(electionLbl)
        
        padLbl = Label(text="",
                       size_hint=(None,None),
                       size=(self.width, self.height/16))
        self.ids.grid.add_widget(padLbl)
        
        # temp grid layout for button alignment
        tmpGridLayout = GridLayout(cols=4)
        
        finishBtn = Button(text="Cancel",
                           size_hint=(None,None),
                           size=(self.width/4, self.height/8))
        finishBtn.bind(on_press=self.backBtn)
        
        tmpGridLayout.add_widget(finishBtn)
        padLbl = Label(text="",
                       size_hint=(None,None),
                       size=(self.width/4, self.height/8))
        tmpGridLayout.add_widget(padLbl)
        
        padLbl = Label(text="",
                       size_hint=(None,None),
                       size=(self.width/4, self.height/8))
        tmpGridLayout.add_widget(padLbl)
        
        finishBtn = Button(text="Cast Vote",
                           size_hint=(None,None),
                           size=(self.width/4, self.height/8))
        finishBtn.bind(on_press=partial(self.confVote, voter_id, election_id, vote_select, index_choice))
        tmpGridLayout.add_widget(finishBtn)
        self.ids.grid.add_widget(tmpGridLayout)

#Manager to handle all possible screens
#---------------------------------------
class WindowManager(ScreenManager):
    vm_home = ObjectProperty(None)
    vm_election_list = ObjectProperty(None)
    vm_election_det = ObjectProperty(None)
    vm_vote_confirm = ObjectProperty(None)

kv = Builder.load_file("vm_home.kv")

#Loads the Home Screen
#---------------------------------------
class VM_HomeApp(App):
    elec_id = 0
    elec_name = 0
    voter_id = 0
    vote_select = 0
    index_choice = 0
    token = 0
    
    def build(self):
        return kv

if __name__ == "__main__":
    Config.set('graphics', 'fullscreen', 'auto')
    Config.set('graphics', 'window_state', 'maximized')
    Config.write()

    VM_HomeApp().run()