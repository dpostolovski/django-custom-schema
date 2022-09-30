class CustomSchema(AutoSchema):
    def __init__(self, *args, **kwargs):
        super(CustomSchema, self).__init__(*args, **kwargs)

        self.custom_serializers = set()

    def get_operation_id_base(self, path, method, action):
        name = self.view.__class__.__name__
        if name.lower().endswith('viewset'):
            name = name[:-7]
        elif name.lower().endswith('view'):
            name = name[:-4]

            if name.endswith(action.title()):  # ListView, UpdateAPIView, ThingDelete ...
                name = name[:-len(action)]

        if action == 'list' and not name.endswith('s'):  # listThings instead of listThing
            name += 's'
        return name

    def get_components(self, path, method):
        components = super(CustomSchema, self).get_components(path, method)

        custom_list_serializers = list(self.custom_serializers)
        for serializer in custom_list_serializers:
            component_name = self.get_component_name(serializer)
            content = self.map_serializer(serializer)
            components.setdefault(component_name, content)
        return components

    def traverse_child(self, child):
        for field in child.fields.fields.values():
            if isinstance(field, serializers.Serializer):
                self.custom_serializers.add(field)
                self.traverse_child(field)

            if isinstance(field, serializers.ListSerializer):
                self.custom_serializers.add(field.child)
                self.traverse_child(field.child)

    def map_field(self, field):
        if isinstance(field, serializers.Serializer):
            self.traverse_child(field)
            return self.get_reference(field)

        if isinstance(field, serializers.ListSerializer):
            self.custom_serializers.add(field.child)
            self.traverse_child(field.child)

            return {
                'type': 'array',
                'items': {**self.get_reference(field.child)}
            }

        return super(CustomSchema, self).map_field(field)
