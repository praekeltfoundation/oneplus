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

    def get_or_init_instance(self, instance_loader, row):
        row[u'is_staff'] = False

        return super(resources.ModelResource, self) \
            .get_or_init_instance(instance_loader, row)
