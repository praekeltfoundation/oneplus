from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count
from django_boolean_sum import BooleanSum
from organisation.models import Course, Module
from core.models import ParticipantQuestionAnswer, Class, Learner
from filters import get_timeframe_range


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

        return ans["total"], ans["correct"], ans["total"] - ans["correct"]

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

    def make_result_datiod(self, num, total, name):
        perc = 0

        if total > 0:
            perc = num * 100 / total

        return {
            "large": num,
            "small": perc,
            "name": name
        }

    def get_active_user_data(self, tf_start, tf_end, cls, total):
        num = self.get_total_active_users_per_class(tf_start, tf_end, cls)
        return self.make_result_datiod(num, total, "Active Users")

    def get_inactive_user_data(self, tf_start, tf_end, cls, total):
        num = self.get_total_inactive_users_per_class(tf_start, tf_end, cls)
        return self.make_result_datiod(num, total, "Inactive Users")

    def get_questions_answered_data(self, total, num):
        return self.make_result_datiod(num, total, "Questions Answered")

    def get_questions_correct_data(self, total, num):
        return self.make_result_datiod(num, total, "Questions Correct")

    def get_questions_incorrect_data(self, total, num):
        return self.make_result_datiod(num, total, "Questions Incorrect")

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

        if state["id"] == 2:
            mr = ParticipantQuestionAnswer.objects.all()

            module = self.get_module(module_filter)
            modules = self.get_modules(course, module)

            if module:
                mr = mr.filter(question__module__pk=module)

            if tf_start and tf_end:
                mr = mr.filter(answerdate__range=[tf_start, tf_end])

            module_results = list(
                mr.values("question__name")
                .annotate(num_answers=Count("pk"))
                .annotate(num_correct=BooleanSum("correct"))
                .order_by("question__name")
            )

            for result in module_results:
                if result["num_answers"] is not None and result["num_answers"] > 0:
                    result["perc"] = result["num_correct"] * 100 / result["num_answers"]

        if state["id"] == 3:
            """
            * Active Users
                * Large Text: Shows total active users for time period selected.
                * Small Text: Shows percentage of total users active
            * Inactive Users
                * Large Text: Shows total inactive users for time period selected.
                * Small Text: Shows percentage of total users inactive for time period selected.
            * Questions Answered
                * Large Text: Shows total answers for time period selected.
                * Small Text: Shows percentage of total questions answered for time period selected.
            * Questions Correct
                * Large Text: Shows percentage correct answers for time period selected
                * Small Text: Shows total correct answers for time period selected.
            * Questions Incorrect
                * Large Text: : Shows percentage incorrect answers for time period selected.
                * Small Text: Shows total incorrect answers for time period selected.
            * Questions Correct per Module (Each module has an individual text display)
                * Large Text: Shows percentage correct answers for time period selected
                * Small Text: Shows total correct answers for time period selected.
            """
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
                result = {
                    "name": cls.name,
                    "results": [
                        self.get_active_user_data(tf_start, tf_end, cls, total_active_learners),
                        self.get_inactive_user_data(tf_start, tf_end, cls, total_inactive_learners),
                        self.get_questions_answered_data(total_questions, num_questions),
                        self.get_questions_correct_data(total_correct, num_correct),
                        self.get_questions_incorrect_data(total_incorrect, num_incorrect),
                    ]
                }

                for md in modules:
                    num_questions, num_correct, num_incorrect = \
                        self.get_total_questions_per_class_per_module(tf_start, tf_end, cls, md)

                    result["results"].append(
                        self.make_result_datiod(
                            num_correct,
                            total_module_results[md.id]["total_correct"],
                            md.name
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