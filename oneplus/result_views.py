from django.shortcuts import render
from django.views.generic import View
from django.db.models import Count
from organisation.models import Course, Module
from core.models import ParticipantQuestionAnswer
from django_boolean_sum import BooleanSum


class ResultsView(View):
    states = [
        {"id": 1, "name": "Activity"},
        {"id": 2, "name": "Question Results"},
        {"id": 3, "name": "Class Results"},
    ]

    default_state = 0
    default_timeframe = 4

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
        if module is None or module == "0":
            return None

        return module

    def get_timeframes(self, timeframe):
        return []

    def get(self, request, course):

        course_obj = self.get_course(course)

        return render(
            request,
            "admin/results/results.html",
            {
                "course": course_obj,
                "state": self.get_state(self.default_state)
            }
        )

    def post(self, request, course):

        course_obj = self.get_course(course)
        state = self.get_state(self.default_state)
        module = None
        modules = None
        module_results = None
        timeframes = self.get_timeframes(self.default_timeframe)

        if "state" in request.POST.keys():
            state = self.get_state(request.POST["state"])

        if "module" in request.POST.keys():
            module = self.get_module(request.POST["module"])

        if state["id"] == 2:
            modules = Module.objects.filter(coursemodulerel__course=course).values("id", "name")
            mr = ParticipantQuestionAnswer.objects.all()

            if module:
                mr.filter(question__module=module)

            module_results = mr.annotate(num_questions=Count("pk"))\
                .annotate(num_correct=BooleanSum("correct"))\
                .order_by("question__name")\
                .values("question__name", "num_questions", "num_correct")


        return render(
            request,
            "admin/results/results.html",
            {
                "course": course_obj,
                "state": state,
                "modules": modules,
                "module_results": module_results,
                "timeframes": timeframes
            }
        )