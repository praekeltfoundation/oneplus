from import_export import resources
from organisation.models import Organisation, School


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

    def import_obj(self, obj, data, dry_run):
        if 'organisation' in data and data['organisation']:
            try:
                data['organisation'] = int(data['organisation'])
            except:
                try:
                    data['organisation'] = Organisation.objects.get(name=data['organisation']).pk
                except:
                    raise

        if 'open_type' in data and data['open_type']:
            try:
                data['open_type'] = int(data['open_type'])
            except:
                for ot in School.OPEN_TYPE_CHOICES:
                    if data['open_type'] == ot[1]:
                        data['open_type'] = ot[0]

        return super(resources.ModelResource, self).import_obj(obj, data, dry_run)

    def skip_row(self, instance, original):
        return School.objects.filter(name=instance.name).exists()
