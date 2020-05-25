from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from declare_database import Person, Question, Habits, Base
from datetime import date,timedelta, datetime
import random
import plotly.graph_objects as go


class DatabaseHelper:

    def __init__(self):

        self.engine = create_engine('sqlite:///janusz_database.db',connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        Base.metadata.bind = self.engine
        self.DBSession = sessionmaker(bind=self.engine)
        self.k = 3

    def visualise(self,sender,day):

        session = self.DBSession()
        headerColor = 'grey'
        rowEvenColor = 'lightgrey'
        rowOddColor = 'white'

        habits = self.download_habit_list(sender)
        print(habits)
        week_table =[]
        day_list = []
        week_day = datetime.weekday(day)
        monday = day - timedelta(days=week_day)
        week = str(monday)+" - "+str(monday+timedelta(days=6))

        if session.query(Person).filter(Person.sender_id.like(sender)).first():
            id_of_a_person =session.query(Person).filter(Person.sender_id.like(sender)).first().id

            for day in range(0,7):
                date_log = str(monday+timedelta(days=day))
                if len(session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.date_done.like(date_log)).all()) !=0:
                    day_list=[]
                    for i in range (0,len(habits)):
                        qid=session.query(Question).filter(Question.question.like(habits[i]), Question.person_id.like(id_of_a_person)).first().id
                        if session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.date_done.like(date_log), Habits.question_id.like(qid)).first():
                            if session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.date_done.like(date_log), Habits.question_id.like(qid)).first().if_done == "1":
                                day_list.append("V")
                            else:
                                day_list.append("X")
                        else:
                            day_list.append("")
                else:
                    day_list=len(habits)*[""]
                print(day_list)
                week_table.append(day_list)

            print(week_table)

            fig = go.Figure(data=[go.Table(
              header=dict(
                values=['<b>Habits for week {}</b>'.format(week),'<b>Pon</b>','<b>Wt</b>','<b>Sr</b>','<b>Czw</b>','<b>Pt</b>','<b>Sb</b>','<b>Nd</b>'],
                line_color='darkslategray',
                fill_color=headerColor,
                align=['left','center'],
                font=dict(color='white', size=12)
              ),
              cells=dict(
                values=[
                  habits,
                  week_table[0],
                  week_table[1],
                  week_table[2],
                  week_table[3],
                  week_table[4],
                  week_table[5],
                  week_table[6]],
                line_color='darkslategray',
                # 2-D list of colors for alternating rows
                fill_color = [[rowOddColor,rowEvenColor,rowOddColor, rowEvenColor,rowOddColor]*5],
                align = ['left', 'center'],
                font = dict(color = 'darkslategray', size = 11)
                ))
            ])

            table_image = "images/{}.jpeg".format(str(sender)+"-"+str(week))
            fig.write_image(table_image)

            return table_image

    def get_person(self, id):

        session = self.DBSession()
        query = session.query(Person).filter(Person.sender_id.like(id))
        if query.first():
            return query.first()
        else:
            return None

    def save_question_into_table(self, a_question,tag,id):

        session = self.DBSession()
        if self.get_person(id) is None:
            print("Adding person with id : ", id, " into database")
            session.add(Person(sender_id= id))
            session.commit()
            print("Person added")

        id_of_a_person =session.query(Person).filter(Person.sender_id.like(id)).first().id

        question_log = Question(question=a_question, time_tag = tag, person_id=id_of_a_person)
        print("Adding", a_question,"with tag",tag,"of person with id: ",id, " into database")
        session.add(question_log)
        print("Question added into database")
        session.commit()

    def del_question_from_table(self, a_question,id):

        session = self.DBSession()
        id_of_a_person =session.query(Person).filter(Person.sender_id.like(id)).first().id

        print("Deleting --",a_question, "-- from database")
        if session.query(Question).filter_by(question=a_question,person_id=id_of_a_person).first():
            get_id = session.query(Question).filter_by(question=a_question, person_id=id_of_a_person).first()
            i_d= int(get_id.id)
            print("question id is:",i_d)
            session.query(Habits).filter_by(question_id=i_d).delete()
            session.query(Question).filter_by(question=a_question,person_id=id_of_a_person).delete()
            session.commit()
            return "Deleted from the database"
        else:
            return "Please enter correct habit name"

    def delete_all_person_questions(self,sender):

        session = self.DBSession()
        print("id to :", sender)

        if session.query(Person).filter(Person.sender_id.like(sender)).first():
            id_of_a_person =session.query(Person).filter(Person.sender_id.like(sender)).first().id
            print("Deleting all questions belonging to user ", sender," from database")

            if session.query(Question).filter_by(person_id=id_of_a_person).first():
                count = session.query(Question).filter_by(person_id=id_of_a_person).count()
                for i in range(0,count):
                    get_id = session.query(Question).filter_by(person_id=id_of_a_person).first()
                    i_d= int(get_id.id)
                    print("question id is:",i_d)
                    session.query(Habits).filter_by(question_id=i_d).delete()
                    session.query(Question).filter_by(id=i_d).delete()
                    session.commit()
                print("Database is empty for user with id", sender)
                return "History deleted"
            else:
                print("Nothing to delete")
                return "List of habits was empty"

        return "Person not in database"

    def save_habit_into_table(self,a_question, done, when, sender_id):

        session = self.DBSession()
        id_of_person = self.get_person(sender_id).id

        def get_question_id(a_question,id_of_person):
            query = session.query(Question).filter(Question.question.like(a_question),Question.person_id.like(id_of_person))
            if query.first():
                return query.first().id
            else:
                return None

        habit_log = Habits(question_id=get_question_id(a_question,id_of_person), if_done= done, date_done= when, person_id=id_of_person)
        print("Adding answer to --",a_question,"-", when , "-- into database")
        session.add(habit_log)
        print("Habit log added into database")
        session.commit()


    def download_habit_list(self,sender):

        session = self.DBSession()
        list_of_habits=[]

        if session.query(Person).filter(Person.sender_id.like(sender)).first():
            id_of_a_person =session.query(Person).filter(Person.sender_id.like(sender)).first().id

            if session.query(Question).first():
                count = session.query(Question).filter(Question.person_id.like(id_of_a_person)).count()
                all = session.query(Question).filter(Question.person_id.like(id_of_a_person)).all()
                for i in range(0,count):
                    item = all[i].question
                    list_of_habits.append(item)

        return list_of_habits

    def download_habit_list_today(self,id):

        session = self.DBSession()

        list_of_habits=[]
        today=date.today()

        if session.query(Person).filter(Person.sender_id.like(id)).first():
            id_of_a_person =session.query(Person).filter(Person.sender_id.like(id)).first().id
            print("id of that instance of person with sender id:",id,"is", id_of_a_person)

            if session.query(Question).first():
                count = session.query(Question).filter(Question.person_id.like(id_of_a_person)).count()
                questions_person = session.query(Question).filter(Question.person_id.like(id_of_a_person)).all()
                for i in range(0,count):
                    question = questions_person[i].id
                    if session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.question_id.like(question)):
                        habit_log_count = session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.question_id.like(question)).count()
                        habits_logged_done = session.query(Habits).filter(Habits.person_id.like(id_of_a_person),Habits.question_id.like(question),
                        Habits.date_done.like(today), Habits.if_done.like(1)).count()
                    if habits_logged_done !=0:
                        pass
                    else:
                        q = session.query(Question).filter(Question.id.like(question)).first().question
                        list_of_habits.append(q)

        return list_of_habits


    def download_stats(self,days_count,id):

        session = self.DBSession()
        start_date = date.today()-timedelta(days=(int(days_count)-1))
        end_date =date.today()
        end_date_range = date.today()+timedelta(days=1)

        def daterange(start_date, end_date):
            for n in range(int ((end_date - start_date).days)):
                yield start_date + timedelta(n)

        id_num=session.query(Question).count()
        result=[]
        id_of_a_person =session.query(Person).filter(Person.sender_id.like(id)).first().id

        if session.query(Question).first():
            count = session.query(Question).filter(Question.person_id.like(id_of_a_person)).count()
            all = session.query(Question).filter(Question.person_id.like(id_of_a_person)).all()
            for i in range(0,count):
                q = all[i].question
                q_id = all[i].id
                habit_count = 0
                for single_date in daterange(start_date, end_date_range):
                    if session.query(Habits).filter(Habits.date_done.like(single_date),Habits.question_id.like(q_id),Habits.if_done.like(1), Habits.person_id.like(id_of_a_person)).first():
                        habit_count+=1
                if habit_count == 0:
                    habit_stat = "Unfortunately in the last "+str(days_count)+" days you did not manage to do "+str(q)
                else:
                    habit_stat = "You managed to do "+q+" "+str(habit_count)+" times in the last "+str(days_count)+" days"
                result.append(habit_stat)

        return result

    def download_selected_habits(self,tag,id):

        session = self.DBSession()
        list_of_habits=[]
        today=date.today()
        print("tag : ", tag)

        if session.query(Person).filter(Person.sender_id.like(id)).first():
            id_of_a_person =session.query(Person).filter(Person.sender_id.like(id)).first().id
            print("id of that instance of person with sender id:",id,"is", id_of_a_person)

            if session.query(Question).first():
                count_tag = session.query(Question).filter(Question.person_id.like(id_of_a_person),Question.time_tag.like(tag)).count()
                print("Number of questions with tag" ,tag, ":", count_tag)
                count_no_tag = session.query(Question).filter(Question.person_id.like(id_of_a_person),Question.time_tag.like(0)).count()
                print("Number of questions with tag 0" , count_no_tag)
                questions_person_tag = session.query(Question).filter(Question.person_id.like(id_of_a_person),Question.time_tag.like(tag)).all()
                questions_person_no_tag = session.query(Question).filter(Question.person_id.like(id_of_a_person),Question.time_tag.like(0)).all()

                for i in range(0,count_tag):
                    question = questions_person_tag[i].id
                    if session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.question_id.like(question)):
                        habit_log_count = session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.question_id.like(question)).count()
                        print("Saved",habit_log_count, "logs of question",questions_person_tag[i].question)
                        habits_logged_done = session.query(Habits).filter(Habits.person_id.like(id_of_a_person),Habits.question_id.like(question),
                        Habits.date_done.like(today), Habits.if_done.like(1)).count()
                    if habits_logged_done !=0:
                        pass
                    else:
                        q = session.query(Question).filter(Question.id.like(question)).first().question
                        list_of_habits.append(q)
                    print("Number of habits with tag ",tag ,":", list_of_habits)

                for i in range(0,count_no_tag):
                    question = questions_person_no_tag[i].id
                    if session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.question_id.like(question)):
                        habit_log_count = session.query(Habits).filter(Habits.person_id.like(id_of_a_person), Habits.question_id.like(question)).count()
                        print("Saved",habit_log_count, "logs of question",questions_person_no_tag[i].question)
                        habits_logged_done = session.query(Habits).filter(Habits.person_id.like(id_of_a_person),Habits.question_id.like(question),
                        Habits.date_done.like(today), Habits.if_done.like(1)).count()
                    if habits_logged_done !=0:
                        pass
                    else:
                        q = session.query(Question).filter(Question.id.like(question)).first().question
                        list_of_habits.append(q)
                    print("List of habits with added 0 tag questions", list_of_habits)

        return list_of_habits

    def download_k_habits(self,sender):

        session = self.DBSession()
        list_of_habits=[]
        k = 3

        if session.query(Person).filter(Person.sender_id.like(sender)).first():
            id_of_a_person =session.query(Person).filter(Person.sender_id.like(sender)).first().id

            if session.query(Question).first():
                count = session.query(Question).filter(Question.person_id.like(id_of_a_person)).count()
                if count < k :
                    k = count
                all = session.query(Question).filter(Question.person_id.like(id_of_a_person)).all()
                for i in range(0,k):
                    rand = random.randint(0,len(all)-1)
                    item = all[rand].question
                    list_of_habits.append(item)
                    all.remove(all[rand])
        return list_of_habits

    def check_if_in_db(self,a_question, id):

        session = self.DBSession()
        id_of_a_person =session.query(Person).filter(Person.sender_id.like(id)).first().id

        if session.query(Question).filter_by(question=a_question,person_id=id_of_a_person).first():
            return True

        return False
