from import_export import resources
from organisation.models import School


class SchoolResource(resources.ModelResource):
    class Meta:
        model = School
        fields = (
            'id',
            'name',
            'description',
            'organisation',
            'website',
            'email',
            'province',
            'open_type',
        )
        export_order = (
            'id',
            'name',
            'description',
            'organisation',
            'website',
            'email',
            'province',
            'open_type',
        )

    def dehydrate_organisation(self, school):
        if school.organisation:
            return school.organisation.name
        else:
            return ''

    def dehydrate_open_type(self, school):
        for ot in School.OPEN_TYPE_CHOICES:
            if school.open_type == ot[0]:
                return ot[1]
        return ''
