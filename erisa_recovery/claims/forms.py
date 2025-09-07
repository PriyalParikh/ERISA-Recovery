from django import forms

class ClaimsUploadForm(forms.Form):
    claims_file = forms.FileField(label="Claims File (CSV or JSON)")
    details_file = forms.FileField(label="Details File (CSV or JSON)")
    MODE_CHOICES = [
        ("overwrite", "Overwrite (replace all data)"),
        ("append", "Append (add/update only)")
    ]
    mode = forms.ChoiceField(choices=MODE_CHOICES, initial="overwrite", widget=forms.RadioSelect)
