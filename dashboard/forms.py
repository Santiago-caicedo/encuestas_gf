import re
from django import forms
from django.core.exceptions import ValidationError
from empresas.models import EmpresaCliente
from django.contrib.auth.models import User
from core.security import validate_hex_color


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = EmpresaCliente
        fields = ['nombre', 'slug', 'aliado', 'logo', 'color_primario', 'email_soporte', 'tiene_sagrilaft', 'tiene_sarlaft', 'tiene_ptee']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded border-gray-300'}),
            'aliado': forms.Select(attrs={'class': 'w-full p-2 border rounded border-gray-300 bg-white'}),
            'slug': forms.TextInput(attrs={'class': 'w-full p-2 border rounded border-gray-300 bg-gray-50'}),
            'email_soporte': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded border-gray-300'}),
            'color_primario': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-0 border-0 cursor-pointer'}),
            'tiene_sagrilaft': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-blue-600 focus:ring-blue-500'}),
            'tiene_sarlaft': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-cyan-600 focus:ring-cyan-500'}),
            'tiene_ptee': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-purple-600 focus:ring-purple-500'}),
        }

    def clean_color_primario(self):
        """SEGURIDAD: Validar que el color sea un hex válido para prevenir CSS injection."""
        color = self.cleaned_data.get('color_primario', '')
        validated_color = validate_hex_color(color)

        # Si el color fue modificado por la validación, significa que no era válido
        if color and color != validated_color and color != '#000000':
            raise ValidationError('El color debe ser un código hexadecimal válido (ej: #FF5733)')

        return validated_color


class NuevoUsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded border-gray-300'}),
        label="Contraseña"
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full p-2 border rounded border-gray-300', 'placeholder': 'Ej: j.perez'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded border-gray-300'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded border-gray-300'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded border-gray-300'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Encriptamos la clave
        user.is_staff = True # LOS MARCAMOS COMO EQUIPO INTERNO
        if commit:
            user.save()
        return user