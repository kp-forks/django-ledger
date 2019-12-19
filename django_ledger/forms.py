from django.forms import (ModelForm, modelformset_factory, BaseModelFormSet,
                          HiddenInput, TextInput, Textarea)
from django.utils.translation import gettext_lazy as _l

from django_ledger.models import (AccountModel, LedgerModel, JournalEntryModel, TransactionModel,
                                  ChartOfAccountModel, EntityModel)
from django_ledger.models.mixins.io import validate_tx_data

# todo: move this to settings...
DJETLER_FORM_INPUT_CLASS = 'input'


class EntityModelForm(ModelForm):
    class Meta:
        model = EntityModel
        fields = [
            'name',
        ]
        labels = {
            'name': _l('Entity Name')
        }
        widgets = {
            'name': TextInput(
                attrs={
                    'class': DJETLER_FORM_INPUT_CLASS,
                    'placeholder': _l('Entity name...')
                }
            )
        }


class ChartOfAccountsModelForm(ModelForm):
    class Meta:
        model = ChartOfAccountModel
        fields = [
            'slug',
            'name',
            'description'
        ]
        labels = {
            'slug': _l('CoA ID'),
            'name': _l('Name'),
            'description': _l('Description'),
        }
        widgets = {
            'slug': TextInput(attrs={
                'class': DJETLER_FORM_INPUT_CLASS
            }),
            'name': TextInput(attrs={
                'class': DJETLER_FORM_INPUT_CLASS
            }),
            'description': Textarea(attrs={
                'class': DJETLER_FORM_INPUT_CLASS
            }),
        }


class AccountModelBaseForm(ModelForm):
    """"""

    def __init__(self, coa_slug, entity_slug, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.COA_SLUG = coa_slug
        self.ENTITY_SLUG = entity_slug
        self.fields['parent'].queryset = self.fields['parent'].queryset.filter(
            coa__slug__exact=self.COA_SLUG,
        ).order_by('code')


class AccountModelCreateForm(AccountModelBaseForm):
    class Meta:
        model = AccountModel
        fields = [
            'parent',
            'code',
            'name',
            'role',
            'balance_type',
        ]


class AccountModelUpdateForm(AccountModelBaseForm):

    def __init__(self, coa_slug, entity_slug, *args, **kwargs):
        super().__init__(coa_slug=coa_slug, entity_slug=entity_slug, *args, **kwargs)
        self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
            id=self.instance.id
        )

    class Meta:
        model = AccountModel
        fields = [
            'parent',
            'code',
            'name',
            'locked',
            'active'
        ]


class LedgerModelCreateForm(ModelForm):
    class Meta:
        model = LedgerModel
        fields = [
            'entity',
            'name',
        ]


class LedgerModelUpdateForm(ModelForm):
    class Meta:
        model = LedgerModel
        fields = [
            'entity',
            'name',
            'posted',
            'locked',
        ]


class JournalEntryModelForm(ModelForm):
    class Meta:
        model = JournalEntryModel
        fields = [
            'ledger',
            'parent',
            'activity',
            'date',
            'description'
        ]


class TransactionModelForm(ModelForm):
    class Meta:
        model = TransactionModel
        fields = [
            'id',
            'account',
            'tx_type',
            'amount',
            'description'
        ]
        widgets = {
            'id': HiddenInput(),
            'journal_entry': HiddenInput()
        }


class BaseTransactionModelFormSet(BaseModelFormSet):

    def clean(self):
        if any(self.errors):
            return
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
        txs_balances = [{
            'tx_type': tx.cleaned_data.get('tx_type'),
            'amount': tx.cleaned_data.get('amount')
        } for tx in self.forms if not self._should_delete_form(tx)]
        validate_tx_data(txs_balances)


TransactionModelFormSet = modelformset_factory(
    model=TransactionModel,
    form=TransactionModelForm,
    formset=BaseTransactionModelFormSet,
    can_delete=True,
    extra=5)