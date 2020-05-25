import joke as random_joke
import urllib.request, urllib.parse, urllib.error
import ssl
import re

from datetime import date,timedelta, datetime
import re

class Janusz:

    def __init__(self,DH,sender):
        self.id = sender
        self.DH = DH

        self.state = False

        self.when=date.today()
        self.state_time = datetime.now()
        self.yesterday = date.today() - timedelta(days=1)
        self.day_of_week = datetime.weekday(date.today())
        self.chat_state=-1
        self.tag_add_answer = 0

        self.list_for_tomorrow = self.DH.download_k_habits(self.id)
        self.list_for_today=[]

    def check_timeout(self):
        now = datetime.now()
        if now > self.state_time + timedelta(hours=4):
            self.state = False

    def visualise(self):
        return self.DH.visualise(self.id,self.when)

    def ask_habits(self,msg):
        if msg is not False:
            if 'Habit check' in msg:
                self.state = "habit"
                self.state_time=datetime.now()
                return True
            return False

    def table(self,msg):
        if "table" in msg:
            self.state="table"
            return True

    def send_table(self):
        self.state= False
        #Under development
        return "https://upload.wikimedia.org/wikipedia/commons/c/c5/Paperclip_icon.png"

    def new_day(self):
        self.list_for_today = self.list_for_tomorrow
        self.list_for_tomorrow = []
        self.state = "k habit"
        self.state_time=datetime.now()
        return "Hi! Have you managed to do:"

    def ask_for_next_day(self):
        self.state = "tomorrow"
        self.state_time=datetime.now()
        return "What do ask you about tomorrow? Press thumbs up if same as today"

    def ask_for_list_for_tomorrow(self,msg):
        if msg == "yes":
            self.state = False
            self.list_for_tomorrow = self.list_for_today
            return "OK! You are all set"
        else:
            if self.DH.check_if_in_db(msg,self.id) is True:
                self.list_for_tomorrow.append(msg)
                return "Saved! Choose another habit or press thumbs up if that is all"
            elif "add" in msg:
                print("Add to habits request")
                new_question = re.findall("add.(.+)",msg)[0]
                self.DH.save_question_into_table(new_question, 0 ,self.id)
                return "Saved! Choose another habit or press thumbs up if that is all""
            elif msg == "":
                pass
            else:
                return "Input correct habit or add new habit typing 'add' and your new habit"

    def ask_for_tag(self):
        return "Do you want to assign a time for your habit? Type m for morning, a for afternoon and e for evening"

    def ask_tag_habits(self,msg):
        if msg == "morning":
            self.tag = "m"
            self.state = "habit tag"
            self.state_time=datetime.now()
            return True
        elif msg =="afternoon":
            self.tag = "a"
            self.state = "habit tag"
            self.state_time=datetime.now()
            return True
        elif msg == "evening":
            self.tag = "e"
            self.state = "habit tag"
            self.state_time=datetime.now()
            return True
        else:
            return False

    def is_not_done(self,msg):
        if msg is not False:
            if 'not done' in msg:
                return True
            return False

    def is_yes (self, msg):
        if self.state is not False:
            if 'yes' == msg or 'yes' == msg or msg == 369239263222822:
                if self.state == "habit" or self.state == "habit_tag" :
                    self.save_habit_log_yes(self.habit,self.when)
                if self.state == "k habit":
                    self.save_habit_log_yes(self.habit,self.yesterday)
                return True
        return False

    def is_no (self, msg):
        if 'no' == msg or 'no' == msg:
            if self.state == "habit" or self.state == "habit_tag":
                self.save_habit_log_no(self.habit,self.when)
                return True
            if self.state == "k habit":
                self.save_habit_log_no(self.habit,self.yesterday)
                return True
        return False

    def joke_response(self,msg):
        if msg != "":
            if self.state == "joke":
                if self.is_yes(msg) == True:
                    pass
                else:
                    self.state = "ask_for_next_day"
                    self.no_joke = "Too bad!"
                    return True
            return False

    def is_add(self,msg):
        if "add" in msg:
            self.state = "tag"
            self.state_time=datetime.now()
            print("Add habit request")
            self.new_habit = re.findall("add.(.+)",msg)[0]
            print(self.new_habit)
            return True
        return False


    def is_add_tag(self,msg):
        if self.state == "tag":
            if msg =="":
                return False
            if (msg == "a") or (msg == "m") or (msg == "e"):
                self.tag_add_answer = msg
            else:
                self.tag_add_answer = 0
            return True
        else:
            return False

    def is_delete(self,msg):
        if "delete" in msg:
            return True
        return False

    def is_show(self,msg):
        if "show habits" in msg:
            return True
        else:
            return False

    def is_show_stats(self, msg):
        if "statist" in msg:
            return True
        else:
            return False

    def stats_days(self,msg):
        if len(re.findall("(\d).days",msg)) > 0:
            return re.findall("(\d).days",msg)[0]
        return 7

    def is_reset_person_questions(self,msg):
        if "reset" in msg:
            return True
        else:
            return False

    def janusz_response(self):

        if self.state == "habit":
            self.questions_to_ask()
            q_lst = self.download_questions
            state = self.updated_chat_state()
            print("status nr",state)
            if len(q_lst) == 0:
                self.chat_state = -1
                self.state = "joke"
                self.state_time=datetime.now()
                return "Good job! All habits complete today. Do you want to hear a joke?"
            elif state < len(q_lst):
                self.habit = q_lst[state]
                return q_lst[state]
            else:
                self.chat_state = -1
                self.state = False
                self.update_habit_list()
                if self.if_all_done() is not False:
                    self.state = "joke"
                    self.state_time=datetime.now()
                    return "Good job! All habits complete today. Do you want to hear a joke?"
                return "Thanks for the answers!"

        if self.state == "habit tag":
            self.questions_to_ask_2(self.tag)
            q_lst = self.download_tag_questions
            state = self.updated_chat_state()
            print("state nr",state)
            if len(q_lst) == 0:
                self.chat_state=-1
                self.state = "joke"
                self.state_time=datetime.now()
                return "Good job! All habits complete today. Do you want to hear a joke"
            elif state < len(q_lst):
                self.habit_tag = q_lst[state]
                return q_lst[state]
            else:
                self.chat_state= -1
                self.update_habit_list_2(self.tag,self.id)
                if self.if_all_tag_done(self.tag,self.id) is not False:
                    self.state = "joke"
                    self.state_time=datetime.now()
                    return "Good job! All habits complete today. Do you want to hear a joke?"
                return "Thanks for the answers!"

        if self.state == "k habit":
            q_lst = self.list_for_today
            state = self.updated_chat_state()
            if len(q_lst) == 0:
                self.chat_state = -1
                return "Welcome! Start your journey with Janusz! Please add a new habit "
            elif state < len(q_lst):
                self.habit = q_lst[state]
                return q_lst[state]
            else:
                self.chat_state = -1
                self.state = "joke"
                self.state_time=datetime.now()
                return "Good job! All habits complete today. Do you want to hear a joke?"

        if self.state == "joke" :
            self.state = "ask_for_next_day"
            return random_joke.joke()[0]


    def what_not_done(self):
        self.update_habit_list()
        if len(self.download_questions) == 0:
            return ["All done today"]
        return self.return_habit_list()

    def if_all_done(self):
        print("List of habits",self.return_habit_list())
        if len(self.return_habit_list()) == 0:
            return ("Good job! All habits complete today. Do you want to hear a joke?")
        return False

    def if_all_tag_done(self,tag):
        self.tag = tag
        print("List of outstanding habits with tag",tag, self.return_tag_habits(tag,self.id))
        if len(self.return_tag_habits(tag,self.id)) == 0:
            return ("Good job! All habits complete today. Do you want to hear a joke?")
        return False


    def add_habit(self,msg,tag):
        self.DH.save_question_into_table(self.new_habit, tag ,self.id)
        self.update_habit_list()
        self.state = False
        return "Added to habit list."

    def delete_habits(self,msg):
        print("Habit delete request")
        del_habit = re.findall("usun.(.+)",msg)[0]
        print("Deleting",del_habit)
        deleted = self.DH.del_question_from_table(del_habit,self.id)
        self.update_habit_list()
        return deleted

    def show_habits(self):
        print("Habit list request")
        h_lst = self.DH.download_habit_list(self.id)
        if len(h_lst) == 0:
            return ["There are no habits saved"]
        else:
            return h_lst

    def update_habit_list(self):
        self.download_questions = self.DH.download_habit_list_today(self.id)

    def return_habit_list(self):
        return self.DH.download_habit_list_today(self.id)

    def questions_to_ask(self):
        if self.chat_state == -1:
            self.download_questions = self.DH.download_habit_list_today(self.id)

    def selected_questions(self):
        if self.chat_state == -1:
            self.download_k_questions = self.DH.download_k_habits(self.id)

    def updated_chat_state(self):
        self.chat_state+=1
        return self.chat_state

    def questions_to_ask_2(self,tag):
        if self.chat_state == -1:
            print("chat state -1")
            self.download_tag_questions = self.DH.download_selected_habits(tag,self.id)

    def updated_habit_list_2(self,tag):
        self.download_tag_questions = self.DH.download_selected_habits(tag,self.id)

    def return_tag_habits(self,tag):
        return self.DH.download_selected_habits(tag,self.id)

    def save_habit_log_yes(self,habit,when):
        self.DH.save_habit_into_table(habit,"1",when,self.id)

    def save_habit_log_no(self,habit,when):
        self.DH.save_habit_into_table(habit,"0", when,self.id)

    def show_stats(self,days):
        return self.DH.download_stats(days,self.id)

    def reset_person_questions(self):
        return self.DH.delete_all_person_questions(self.id)
