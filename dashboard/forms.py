from django import forms
from empresas.models import EmpresaCliente
from django.contrib.auth.models import User

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = EmpresaCliente
        fields = ['nombre', 'slug', 'aliado', 'logo', 'color_primario', 'email_soporte', 'tiene_sagrilaft', 'tiene_ptee']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full p-2 border rounded border-gray-300'}),
            'aliado': forms.Select(attrs={'class': 'w-full p-2 border rounded border-gray-300 bg-white'}),
            'slug': forms.TextInput(attrs={'class': 'w-full p-2 border rounded border-gray-300 bg-gray-50'}),
            'email_soporte': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded border-gray-300'}),
            'color_primario': forms.TextInput(attrs={'type': 'color', 'class': 'h-10 w-20 p-0 border-0 cursor-pointer'}),
            'tiene_sagrilaft': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-blue-600 focus:ring-blue-500'}),
            'tiene_ptee': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-purple-600 focus:ring-purple-500'}),
        }


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