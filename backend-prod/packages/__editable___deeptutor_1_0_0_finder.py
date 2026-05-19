from __future__ import annotations
import sys
from importlib.machinery import ModuleSpec, PathFinder
from importlib.machinery import all_suffixes as module_suffixes
from importlib.util import spec_from_file_location
from itertools import chain
from pathlib import Path

MAPPING: dict[str, str] = {'deeptutor': 'D:\\Doubao\\DeepTutor\\deeptutor', 'deeptutor_cli': 'D:\\Doubao\\DeepTutor\\deeptutor_cli'}
NAMESPACES: dict[str, list[str]] = {'deeptutor.utils': ['D:\\Doubao\\DeepTutor\\deeptutor\\utils'], 'deeptutor.agents.research': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\research'], 'deeptutor.agents.chat.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\chat\\prompts'], 'deeptutor.agents.chat.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\chat\\prompts\\en'], 'deeptutor.agents.chat.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\chat\\prompts\\zh'], 'deeptutor.agents.math_animator.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\math_animator\\prompts'], 'deeptutor.agents.math_animator.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\math_animator\\prompts\\en'], 'deeptutor.agents.math_animator.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\math_animator\\prompts\\zh'], 'deeptutor.agents.notebook.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\notebook\\prompts'], 'deeptutor.agents.notebook.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\notebook\\prompts\\en'], 'deeptutor.agents.notebook.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\notebook\\prompts\\zh'], 'deeptutor.agents.question.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\question\\prompts'], 'deeptutor.agents.question.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\question\\prompts\\en'], 'deeptutor.agents.question.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\question\\prompts\\zh'], 'deeptutor.agents.research.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\research\\prompts'], 'deeptutor.agents.research.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\research\\prompts\\en'], 'deeptutor.agents.research.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\research\\prompts\\zh'], 'deeptutor.agents.solve.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\solve\\prompts'], 'deeptutor.agents.solve.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\solve\\prompts\\en'], 'deeptutor.agents.solve.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\solve\\prompts\\zh'], 'deeptutor.agents.vision_solver.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\vision_solver\\prompts'], 'deeptutor.agents.visualize.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\visualize\\prompts'], 'deeptutor.agents.visualize.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\visualize\\prompts\\en'], 'deeptutor.agents.visualize.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\agents\\visualize\\prompts\\zh'], 'deeptutor.api.utils': ['D:\\Doubao\\DeepTutor\\deeptutor\\api\\utils'], 'deeptutor.book.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\book\\prompts'], 'deeptutor.book.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\book\\prompts\\en'], 'deeptutor.book.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\book\\prompts\\zh'], 'deeptutor.co_writer.prompts': ['D:\\Doubao\\DeepTutor\\deeptutor\\co_writer\\prompts'], 'deeptutor.co_writer.prompts.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\co_writer\\prompts\\en'], 'deeptutor.co_writer.prompts.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\co_writer\\prompts\\zh'], 'deeptutor.services.llm.providers': ['D:\\Doubao\\DeepTutor\\deeptutor\\services\\llm\\providers'], 'deeptutor.tools.prompting.hints': ['D:\\Doubao\\DeepTutor\\deeptutor\\tools\\prompting\\hints'], 'deeptutor.tools.prompting.hints.en': ['D:\\Doubao\\DeepTutor\\deeptutor\\tools\\prompting\\hints\\en'], 'deeptutor.tools.prompting.hints.zh': ['D:\\Doubao\\DeepTutor\\deeptutor\\tools\\prompting\\hints\\zh'], 'deeptutor.tutorbot.skills': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills'], 'deeptutor.tutorbot.skills.clawhub': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\clawhub'], 'deeptutor.tutorbot.skills.cron': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\cron'], 'deeptutor.tutorbot.skills.deep-question': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\deep-question'], 'deeptutor.tutorbot.skills.deep-research': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\deep-research'], 'deeptutor.tutorbot.skills.deep-solve': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\deep-solve'], 'deeptutor.tutorbot.skills.github': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\github'], 'deeptutor.tutorbot.skills.knowledge-base': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\knowledge-base'], 'deeptutor.tutorbot.skills.memory': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\memory'], 'deeptutor.tutorbot.skills.notebook': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\notebook'], 'deeptutor.tutorbot.skills.skill-creator': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\skill-creator'], 'deeptutor.tutorbot.skills.summarize': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\summarize'], 'deeptutor.tutorbot.skills.tmux': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\tmux'], 'deeptutor.tutorbot.skills.weather': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\weather'], 'deeptutor.tutorbot.skills.skill-creator.scripts': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\skill-creator\\scripts'], 'deeptutor.tutorbot.skills.tmux.scripts': ['D:\\Doubao\\DeepTutor\\deeptutor\\tutorbot\\skills\\tmux\\scripts'], 'deeptutor.utils.network': ['D:\\Doubao\\DeepTutor\\deeptutor\\utils\\network']}
PATH_PLACEHOLDER = '__editable__.deeptutor-1.0.0.finder' + ".__path_hook__"


class _EditableFinder:  # MetaPathFinder
    @classmethod
    def find_spec(cls, fullname: str, path=None, target=None) -> ModuleSpec | None:  # type: ignore
        # Top-level packages and modules (we know these exist in the FS)
        if fullname in MAPPING:
            pkg_path = MAPPING[fullname]
            return cls._find_spec(fullname, Path(pkg_path))

        # Handle immediate children modules (required for namespaces to work)
        # To avoid problems with case sensitivity in the file system we delegate
        # to the importlib.machinery implementation.
        parent, _, child = fullname.rpartition(".")
        if parent and parent in MAPPING:
            return PathFinder.find_spec(fullname, path=[MAPPING[parent]])

        # Other levels of nesting should be handled automatically by importlib
        # using the parent path.
        return None

    @classmethod
    def _find_spec(cls, fullname: str, candidate_path: Path) -> ModuleSpec | None:
        init = candidate_path / "__init__.py"
        candidates = (candidate_path.with_suffix(x) for x in module_suffixes())
        for candidate in chain([init], candidates):
            if candidate.exists():
                return spec_from_file_location(fullname, candidate)
        return None


class _EditableNamespaceFinder:  # PathEntryFinder
    @classmethod
    def _path_hook(cls, path) -> type[_EditableNamespaceFinder]:
        if path == PATH_PLACEHOLDER:
            return cls
        raise ImportError

    @classmethod
    def _paths(cls, fullname: str) -> list[str]:
        paths = NAMESPACES[fullname]
        if not paths and fullname in MAPPING:
            paths = [MAPPING[fullname]]
        # Always add placeholder, for 2 reasons:
        # 1. __path__ cannot be empty for the spec to be considered namespace.
        # 2. In the case of nested namespaces, we need to force
        #    import machinery to query _EditableNamespaceFinder again.
        return [*paths, PATH_PLACEHOLDER]

    @classmethod
    def find_spec(cls, fullname: str, target=None) -> ModuleSpec | None:  # type: ignore
        if fullname in NAMESPACES:
            spec = ModuleSpec(fullname, None, is_package=True)
            spec.submodule_search_locations = cls._paths(fullname)
            return spec
        return None

    @classmethod
    def find_module(cls, _fullname) -> None:
        return None


def install():
    if not any(finder == _EditableFinder for finder in sys.meta_path):
        sys.meta_path.append(_EditableFinder)

    if not NAMESPACES:
        return

    if not any(hook == _EditableNamespaceFinder._path_hook for hook in sys.path_hooks):
        # PathEntryFinder is needed to create NamespaceSpec without private APIS
        sys.path_hooks.append(_EditableNamespaceFinder._path_hook)
    if PATH_PLACEHOLDER not in sys.path:
        sys.path.append(PATH_PLACEHOLDER)  # Used just to trigger the path hook
