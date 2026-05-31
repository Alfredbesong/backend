from rest_framework import serializers

from .models import Confirmation, WasteReport


class WasteReportReadSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(source='user.username', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)
    progress_step = serializers.IntegerField(read_only=True)

    class Meta:
        model = WasteReport
        fields = [
            'id',
            'reporter_username',
            'description',
            'photo',
            'latitude',
            'longitude',
            'status',
            'status_label',
            'progress_percent',
            'progress_step',
            'created_at',
            'updated_at',
        ]


class WasteReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteReport
        fields = ['description', 'photo', 'latitude', 'longitude']

    def create(self, validated_data):
        request = self.context['request']
        # The authenticated user owns the report, so the client cannot spoof this field.
        return WasteReport.objects.create(user=request.user, **validated_data)


class WasteReportStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = WasteReport
        fields = ['status']

    def validate_status(self, value):
        allowed = {WasteReport.Status.IN_PROGRESS, WasteReport.Status.RESOLVED}
        if value not in allowed:
            raise serializers.ValidationError('Only admin status updates are allowed.')
        return value


class ConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Confirmation
        fields = ['id', 'report', 'user', 'is_cleared', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
