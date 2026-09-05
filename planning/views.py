from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.forms.models import model_to_dict
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.debug import sensitive_post_parameters

from integrations.hevy import HevyError
from integrations.views import _client_for_request
from planning import proposals
from planning.forms import ImportForm, PromptForm, TrainingProfileForm
from planning.models import PromptGeneration, RoutineProposal, TrainingProfile
from planning.prompts import PromptBuilder


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile, created = TrainingProfile.objects.get_or_create(user=request.user)
        return render(
            request,
            "planning/profile.html",
            {"form": TrainingProfileForm(instance=profile)},
        )

    def post(self, request):
        profile, created = TrainingProfile.objects.get_or_create(user=request.user)
        form = TrainingProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, _("Training profile saved."))
            return redirect("planning:profile")
        return render(request, "planning/profile.html", {"form": form})


class GenerateView(LoginRequiredMixin, View):
    def get(self, request):
        profile = TrainingProfile.objects.filter(user=request.user).first()
        initial = model_to_dict(profile) if profile else {}
        if request.GET.get("duplicate"):
            try:
                initial = get_object_or_404(
                    PromptGeneration, pk=request.GET["duplicate"], user=request.user
                ).inputs
            except ValidationError:
                raise Http404 from None
        return render(
            request, "planning/generate.html", {"form": PromptForm(initial=initial)}
        )

    def post(self, request):
        form = PromptForm(request.POST)
        context = {"form": form}
        account = getattr(request.user, "hevy_account", None)
        if not account:
            form.add_error(
                None, _("Connect Hevy before generating a prompt.")
            ) if form.is_bound and form.is_valid() else None
        elif form.is_valid():
            builder = PromptBuilder(account)
            try:
                text, manifest = builder.build(form.cleaned_data)
                context.update(
                    {
                        "preview": text,
                        "manifest": manifest,
                        "signature": signing.dumps(
                            [request.user.pk, manifest["text_hash"]],
                            salt="prompt-preview",
                        ),
                    }
                )
                if request.POST.get("action") == "save":
                    try:
                        valid = signing.loads(
                            request.POST.get("signature", ""),
                            salt="prompt-preview",
                            max_age=900,
                        )
                    except signing.BadSignature:
                        valid = None
                    if valid == [request.user.pk, manifest["text_hash"]]:
                        generation = builder.save(form.cleaned_data, text, manifest)
                        return redirect("planning:generation", pk=generation.pk)
                    form.add_error(
                        None,
                        _(
                            "The preview changed or expired. Review the new preview before saving."
                        ),
                    )
            except ValueError as error:
                form.add_error(None, str(error))
        return render(request, "planning/generate.html", context)


class GenerationListView(LoginRequiredMixin, View):
    def get(self, request):
        items = PromptGeneration.objects.filter(user=request.user)
        return render(
            request,
            "planning/generations.html",
            {"page_obj": Paginator(items, 20).get_page(request.GET.get("page"))},
        )


class GenerationView(LoginRequiredMixin, View):
    def get(self, request, pk):
        generation = get_object_or_404(PromptGeneration, pk=pk, user=request.user)
        if request.GET.get("download") == "1":
            response = HttpResponse(
                generation.text, content_type="text/markdown; charset=utf-8"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="training-prompt-{generation.pk}.md"'
            )
            response["Cache-Control"] = "private, no-store"
            return response
        return render(request, "planning/generation.html", {"generation": generation})

    def post(self, request, pk):
        generation = get_object_or_404(PromptGeneration, pk=pk, user=request.user)
        if request.POST.get("confirm") == "delete":
            generation.delete()
            return redirect("planning:generations")
        return render(request, "planning/delete.html", {"generation": generation})


@method_decorator(sensitive_post_parameters("payload", "file"), name="dispatch")
class ImportView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "planning/import.html", {"form": ImportForm()})

    def post(self, request):
        form = ImportForm(request.POST, request.FILES)
        account = getattr(request.user, "hevy_account", None)
        try:
            proposals.parse_document(request.POST.get('payload', ''))
        except proposals.SecretInputError as error:
            cleared = ImportForm({'payload': ''})
            cleared.is_valid()
            cleared.add_error(None, str(error))
            return render(request, 'planning/import.html', {'form': cleared})
        except ValueError:
            pass
        if form.is_valid():
            try:
                if not account:
                    raise ValueError(_("Connect Hevy before importing a routine."))
                payload = proposals.parse_document(form.cleaned_data["payload"])
                proposal = proposals.preview(
                    account, payload, _client_for_request(request)
                )
                return redirect("planning:proposal", pk=proposal.pk)
            except proposals.SecretInputError as error:
                form = ImportForm({"payload": ""})
                form.is_valid()
                form.add_error(None, str(error))
            except (ValueError, HevyError) as error:
                form.add_error(None, str(error))
        return render(request, "planning/import.html", {"form": form})


class ProposalView(LoginRequiredMixin, View):
    def get(self, request, pk):
        proposal = get_object_or_404(RoutineProposal, pk=pk, account__user=request.user)
        return render(request, "planning/proposal.html", {"proposal": proposal})

    def post(self, request, pk):
        proposal = get_object_or_404(RoutineProposal, pk=pk, account__user=request.user)
        if request.POST.get("confirm") != "apply":
            return redirect("planning:proposal", pk=pk)
        try:
            proposals.submit(proposal.account, pk, _client_for_request(request))
        except (ValueError, HevyError) as error:
            messages.error(request, str(error))
        except DatabaseError:
            messages.error(
                request,
                _(
                    "Local persistence failed. Check the proposal status before taking further action."
                ),
            )
        return redirect("planning:proposal", pk=pk)
