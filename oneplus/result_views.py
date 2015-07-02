from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count
from django_boolean_sum import BooleanSum
from organisation.models import Course, Module
from core.models import ParticipantQuestionAnswer, Class, Learner, Participant
from filters import get_timeframe_range
from calendar import timegm
import json


class ResultsView(View):
    states = [
        {"id": 1, "name": "Activity"},
        {"id": 2, "name": "Question Results"},
        {"id": 3, "name": "Class Results"},
    ]

    default_state = 0
    default_timeframe = 3
    default_module = 0

    def get_course(self, course):
        c = Course.objects.get(pk=course)

        return {
            "name": c.name,
            "id": c.id
        }

    def get_state(self, state):
        i_state = int(state)
        index = self.default_state

        if i_state > 0 and i_state <= len(self.states):
            index = i_state - 1

        return self.states[index]

    def get_module(self, module):
        if module is None:
            return self.default_module

        return int(module)

    def get_modules(self, course, module):
        modules = [{"id": 0, "name": "All"}]
        modules += list(Module.objects.filter(coursemodulerel__course=course).values("id", "name"))

        for temp_module in modules:
            if temp_module["id"] == module:
                temp_module["selected"] = True

        return modules

    def get_timeframe(self, timeframe):
        if timeframe is None:
            return self.default_timeframe

        return int(timeframe)

    def get_timeframes(self, timeframe):
        timeframes = [
            {"id": 0, "name": "All"},
            {"id": 1, "name": "This week"},
            {"id": 2, "name": "Last week"},
            {"id": 3, "name": "This month"},
            {"id": 4, "name": "Last month"},
            {"id": 5, "name": "Last 3 months"},
            {"id": 6, "name": "Last 6 months"},
            {"id": 7, "name": "This year"},
            {"id": 8, "name": "Last year"}
        ]

        for temp_timeframe in timeframes:
            if temp_timeframe["id"] == timeframe:
                temp_timeframe["selected"] = True

        return timeframes

    def get_total_active_users_core(self, learners, tf_start, tf_end):
        if tf_start and tf_end:
            learners = learners.filter(last_active_date__range=[tf_start, tf_end])

        return learners.aggregate(num_active=Count("pk"))["num_active"]

    def get_total_active_users(self, tf_start, tf_end):
        learners = Learner.objects.all()

        return self.get_total_active_users_core(learners, tf_start, tf_end)

    def get_total_active_users_per_class(self, tf_start, tf_end, classs):
        learners = Learner.objects.filter(participant__classs=classs)

        return self.get_total_active_users_core(learners, tf_start, tf_end)

    def get_total_inactive_users_core(self, learners, tf_start, tf_end):
        if tf_start and tf_end:
            learners = learners.exclude(last_active_date__range=[tf_start, tf_end])
        else:
            learners = learners.filter(last_active_date__isnull=True)

        return learners.aggregate(num_inactive=Count("pk"))["num_inactive"]

    def get_total_inactive_users(self, tf_start, tf_end):
        learners = Learner.objects.all()

        return self.get_total_inactive_users_core(learners, tf_start, tf_end)

    def get_total_inactive_users_per_class(self, tf_start, tf_end, classs):
        learners = Learner.objects.filter(participant__classs=classs)

        return self.get_total_inactive_users_core(learners, tf_start, tf_end)

    def get_total_questions_core(self, answers, tf_start, tf_end):
        if tf_start and tf_end:
            answers = answers.filter(answerdate__range=[tf_start, tf_end])

        ans = answers.aggregate(total=Count("pk"), correct=BooleanSum("correct"))

        total = 0
        correct = 0
        incorrect = 0

        if ans["total"]:
            total = ans["total"]

        if ans["correct"]:
            correct = ans["correct"]

        incorrect = total - correct

        return total, correct, incorrect

    def get_total_questions(self, tf_start, tf_end):
        answers = ParticipantQuestionAnswer.objects.all()

        return self.get_total_questions_core(answers, tf_start, tf_end)

    def get_total_questions_per_module(self, tf_start, tf_end, module):
        answers = ParticipantQuestionAnswer.objects.filter(question__module=module)

        return self.get_total_questions_core(answers, tf_start, tf_end)

    def get_total_questions_per_class(self, tf_start, tf_end, cls):
        answers = ParticipantQuestionAnswer.objects.filter(participant__classs=cls)

        return self.get_total_questions_core(answers, tf_start, tf_end)

    def get_total_questions_per_class_per_module(self, tf_start, tf_end, cls, module):
        answers = ParticipantQuestionAnswer.objects.filter(participant__classs=cls, question__module=module)

        return self.get_total_questions_core(answers, tf_start, tf_end)

    def make_result_datiod(self,
                           num,
                           total,
                           name,
                           large_formatter="%s",
                           small_formatter="( %s )",
                           name_formatter="%s",
                           inv=False):
        perc = 0

        if inv is False and total > 0:
            perc = num * 100 / total

        if inv:
            return {
                "large": large_formatter % num,
                "small": small_formatter % total,
                "name": name_formatter % name
            }

        return {
            "large": large_formatter % num,
            "small": small_formatter % perc,
            "name": name_formatter % name
        }

    def get_active_user_data(self, tf_start, tf_end, cls, total):
        num = self.get_total_active_users_per_class(tf_start, tf_end, cls)
        return self.make_result_datiod(num, total, "Active Users", small_formatter="( %s%% )")

    def get_inactive_user_data(self, tf_start, tf_end, cls, total):
        num = self.get_total_inactive_users_per_class(tf_start, tf_end, cls)
        return self.make_result_datiod(num, total, "Inactive Users", small_formatter="( %s%% )")

    def get_questions_answered_data(self, total, num):
        return self.make_result_datiod(num, total, "Questions Answered", small_formatter="( %s%% )")

    def get_questions_correct_data(self, total, perc):
        return self.make_result_datiod(perc, total, "Questions Correct", large_formatter="%s%%", inv=True)

    def get_questions_incorrect_data(self, total, perc):
        return self.make_result_datiod(perc, total, "Questions Incorrect", large_formatter="%s%%", inv=True)

    def get_d3_date(self, date):
        return timegm(date.timetuple())*1000

    def get_data_dict(self, request, course):
        course_obj = self.get_course(course)
        state = self.get_state(self.default_state)
        module = None
        module_filter = None
        modules = None
        module_results = None
        timeframe = None
        timeframes = None
        timeframe_filter = None
        tf_start = None
        tf_end = None
        class_results = None
        activity_results = {
            "activity": {
                "active": [],
                "inactive": []
            },
            "questions": {
                "total": [],
                "correct": [],
                "incorrect": []
            }
        }

        if "state" in request.POST.keys():
            state = self.get_state(request.POST["state"])

        if "module_filter" in request.POST.keys():
            module_filter = request.POST["module_filter"]

        if "timeframe_filter" in request.POST.keys():
            timeframe_filter = request.POST["timeframe_filter"]

        timeframe = self.get_timeframe(timeframe_filter)
        timeframes = self.get_timeframes(timeframe)

        if timeframe > 0:
            tf_start, tf_end = get_timeframe_range(str(timeframe - 1))

        if state["id"] == 1:
            ar_base = ParticipantQuestionAnswer.objects.filter(participant__classs__course__pk=course)\
                .extra(select={"act_date": "date_trunc('day', answerdate)"})
            total_participants = Participant.objects.filter(classs__course__pk=course).count()

            if tf_start and tf_end:
                ar_base = ar_base.filter(answerdate__range=[tf_start, tf_end])

            ar = ar_base.values("act_date")\
                .annotate(num_active=Count("participant", distinct=True))\
                .order_by("act_date")

            active_results = []
            inactive_results = []

            for result in ar:
                d3d = self.get_d3_date(result["act_date"])
                active_results.append({"x": d3d, "y": result["num_active"]})
                inactive_results.append({"x": d3d, "y": total_participants - result["num_active"]})

            activity_results["activity"]["active"] = json.dumps(active_results)
            activity_results["activity"]["inactive"] = json.dumps(inactive_results)

            qa = ar_base.values("act_date")\
                .annotate(total=Count("pk"))\
                .annotate(correct=BooleanSum("correct"))\
                .order_by("act_date")

            qa_total_results = []
            qa_correct_results = []
            qa_incorrect_results = []

            for result in qa:
                d3d = self.get_d3_date(result["act_date"])
                qa_total_results.append({"x": d3d, "y": result["total"]})
                qa_correct_results.append({"x": d3d, "y": result["correct"]})
                qa_incorrect_results.append({"x": d3d, "y": result["total"] - result["correct"]})

            activity_results["questions"]["total"] = json.dumps(qa_total_results)
            activity_results["questions"]["correct"] = json.dumps(qa_correct_results)
            activity_results["questions"]["incorrect"] = json.dumps(qa_incorrect_results)

        if state["id"] == 2:
            mr = ParticipantQuestionAnswer.objects.filter(participant__classs__course__pk=course)

            module = self.get_module(module_filter)
            modules = self.get_modules(course, module)

            if module:
                mr = mr.filter(question__module__pk=module)

            if tf_start and tf_end:
                mr = mr.filter(answerdate__range=[tf_start, tf_end])

            module_results = []

            results = mr.values("question", "question__name")\
                .annotate(num_answers=Count("pk"))\
                .annotate(num_correct=BooleanSum("correct"))\
                .order_by("question__name")

            for result in results:
                perc = 0

                if result["num_answers"] > 0:
                    perc = result["num_correct"] * 100 / result["num_answers"]

                name = "<a href=\"/admin/content/testingquestion/%s/\" target=\"_blank\">%s</a>" \
                       % (result["question"], result["question__name"])

                module_results.append(
                    self.make_result_datiod(
                        result["num_answers"],
                        perc,
                        name,
                        small_formatter="( %s%% correct )",
                        inv=True
                    )
                )

        if state["id"] == 3:
            classes = Class.objects.filter(course__pk=course)
            modules = Module.objects.filter(coursemodulerel__course__pk=course)
            class_results = []
            total_module_results = {}

            total_active_learners = self.get_total_active_users(tf_start, tf_end)
            total_inactive_learners = self.get_total_inactive_users(tf_start, tf_end)
            total_questions, total_correct, total_incorrect = self.get_total_questions(tf_start, tf_end)

            for md in modules:
                num_questions, num_correct, num_incorrect = self.get_total_questions_per_module(tf_start, tf_end, md)
                total_module_results[md.id] = {
                    "total_questions": num_questions,
                    "total_correct": num_correct,
                    "total_incorrect": num_incorrect
                }

            for cls in classes:
                num_questions, num_correct, num_incorrect = self.get_total_questions_per_class(tf_start, tf_end, cls)
                correct_perc = 0
                incorrect_perc = 0

                if num_questions > 0:
                    correct_perc = num_correct * 100 / num_questions
                    incorrect_perc = num_incorrect * 100 / num_questions

                result = {
                    "name": cls.name,
                    "results": [
                        self.get_active_user_data(tf_start, tf_end, cls, total_active_learners),
                        self.get_inactive_user_data(tf_start, tf_end, cls, total_inactive_learners),
                        self.get_questions_answered_data(total_questions, num_questions),
                        self.get_questions_correct_data(total_correct, correct_perc),
                        self.get_questions_incorrect_data(total_incorrect, incorrect_perc),
                    ]
                }

                for md in modules:
                    num_questions, num_correct, num_incorrect = \
                        self.get_total_questions_per_class_per_module(tf_start, tf_end, cls, md)

                    perc_correct = 0

                    if total_module_results[md.id]["total_correct"] > 0:
                        perc_correct = num_correct * 100 / total_module_results[md.id]["total_correct"]

                    result["results"].append(
                        self.make_result_datiod(
                            perc_correct,
                            total_module_results[md.id]["total_correct"],
                            md.name,
                            large_formatter="%s%%",
                            inv=True
                        )
                    )
                class_results.append(result)

        return {
            "course": course_obj,
            "state": state,
            "modules": modules,
            "module_results": module_results,
            "timeframes": timeframes,
            "class_results": class_results,
            "activity_results": activity_results
        }

    def get(self, request, course):

        dd = self.get_data_dict(request, course)

        return render(
            request,
            "admin/results/results.html",
            dd
        )

    def post(self, request, course):

        dd = self.get_data_dict(request, course)

        return render(
            request,
            "admin/results/results.html",
            dd
        )