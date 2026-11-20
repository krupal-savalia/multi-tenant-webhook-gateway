from rest_framework import serializers
from apps.common.validators import validated_target_url

class EndPointSerializer(serializers.Serializer):
    target_url = serializers.URLField(max_length=2048, validators = [validated_target_url])
    subscribed_events = serializers.ListField(
        child=serializers.CharField(max_length=100, allow_blank = False),
        allow_empty = False,
    )

    def validate_subscribed_events(self, value):
        cleaned = [event.strip() for event in value]

        if len(set(cleaned)) != len(cleaned):
            raise serializers.ValidationError("Duplicate events are not allowed.")

        if "*" in cleaned and len(cleaned) > 1:
            raise serializers.ValidationError('Use "*" alone when subscribing to all events.')

        for event in cleaned:
            if event == "*":
                continue

            if "." not in event:
                raise serializers.ValidationError(f"Invalid event name: {event}")
        
        return cleaned