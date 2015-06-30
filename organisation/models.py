from django.db import models

PROVINCE_CHOICES = (
    ("Eastern Cape", "Eastern Cape"),
    ("Free State", "Free State"),
    ("Gauteng", "Gauteng"),
    ("KwaZulu-Natal", "KwaZulu-Natal"),
    ("Limpopo", "Limpopo"),
    ("Mpumalanga", "Mpumalanga"),
    ("North West", "North West"),
    ("Northern Cape", "Northern Cape"),
    ("Western Cape", "Western Cape")
)


class Organisation(models.Model):

    """
    An organisations is a container for schools.
    This exists almost solely for situations where MobileU is deployed as
    a SAAS with multiple organisations on a single server.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    website = models.URLField("Website", max_length=200, blank=True)
    email = models.EmailField("E-Mail", max_length=75, blank=True)
    # schools

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"


class School(models.Model):

    """
    Schools have a name, description and some basic contact details.
    A school manager has the ability to CRUD courses under a school.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    organisation = models.ForeignKey(Organisation, null=True, blank=False)
    website = models.URLField("Website", max_length=200, blank=True)
    email = models.EmailField("E-Mail", max_length=75, blank=True)
    province = models.CharField("Province", max_length=20, null=True, blank=True, choices=PROVINCE_CHOICES)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"


class Course(models.Model):

    """
    Courses have a name, description and slug. A courses manager has the
    ability to CRUD courses content (Modules, Pages & Posts etc). Courses
    additionally have a series of settings which define the 'business
    logic' for a courses.
    """
    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    slug = models.SlugField("Slug", blank=True)
    # The Course can determine the presentation of content.
    # This means a Module and its questions can be presented differently in
    # different courses.
    question_order = models.PositiveIntegerField("Question Order", choices=(
        (1, "Random"), (2, "Ordered"), (3, "Random Intelligent")), default=1)
    is_active = models.BooleanField("Is Active", default=True)

    # modulees
    # pages
    # posts
    # settings

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"


class Module(models.Model):

    """
    Modules have a name, description, learning content, testing content
    and gamification logic.
    """
    NORMAL = 1
    EVENT = 2
    TYPE_CHOICES = (
        (NORMAL, "Normal"),
        (EVENT, "Event")
    )

    name = models.CharField(
        "Name", max_length=500, null=True, blank=False, unique=True)
    description = models.CharField("Description", max_length=500, blank=True)
    courses = models.ManyToManyField(
        Course, related_name='modules', through='CourseModuleRel',)
    is_active = models.BooleanField("Is Active", default=True)
    order = models.IntegerField("Order Number", null=True, blank=True)
    module_link = models.CharField(max_length=500, null=True, blank=True)
    type = models.PositiveIntegerField("Type of Module", choices=TYPE_CHOICES, default=NORMAL)
    # gamification

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"


class CourseModuleRel(models.Model):
    course = models.ForeignKey(Course)
    module = models.ForeignKey(Module)