from django import template
from django.forms.boundfield import BoundField
from django.template.loader import render_to_string
from django.forms.fields import BooleanField

register = template.Library()

@register.filter(is_safe=True)
def validate(field:BoundField):
    if (field):
        if (field.errors):
            init_class = field.field.widget.attrs["class"]
            if (not isinstance(field.field, BooleanField)):
                alert_class = field.field.widget.attrs["class"]+" field-error-border-b"
            else:
                alert_class = field.field.widget.attrs["class"]+" field-error"
            fieldString = field.as_widget(attrs={
                    "x-on:click":"validationError = false",
                    "x-bind:class":"{"+f" '{init_class}': ! validationError, '{alert_class}' : validationError "+"}",
                    "class":alert_class,
            })
            fieldError:str = field.errors.as_text().replace("* ","")
            context:dict = {
                "fieldString": fieldString,
                "fieldError":fieldError
            }
            return render_to_string('errors/fieldValidationError.html', context=context)
    return field


@register.filter(is_safe=True)
def validate_no_error_str(field:BoundField):
    if (field):
        if (field.errors):
            init_class = field.field.widget.attrs["class"]
            alert_class = field.field.widget.attrs["class"]+" field-error"
            fieldString = field.as_widget(attrs={
                    "x-on:click":"validationError = false",
                    "x-bind:class":"{"+f" '{init_class}': ! validationError, '{alert_class}' : validationError "+"}",
                    "class":alert_class,
            })
            context:dict = {
                "fieldString": fieldString
            }
            return render_to_string('errors/fieldValidationError.html', context=context)
    return field