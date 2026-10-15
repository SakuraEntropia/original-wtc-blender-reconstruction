"""Current corrective batch, shared by clean builds and saved-scene migrations."""
from .paving_revision import apply as paving
from .lobby_revision import apply as lobby
from .facade_revision import apply as facade
from .wtc7_roof_revision import apply as roof7
from .crown_edge_revision import apply as crown_junction
from .original_junction_revision import apply as original_junction
from .crown_height_revision import apply as full_crown_height
from .crown_flat_revision import apply as flat_crown
from .oct15_revision import apply as oct15
from .south_roof_revision import apply as south_roof
from .lobby_plan_revision import apply as lobby_plan
from .base_frame_revision import apply as base_frame
from .interior_visibility_revision import apply as interior_visibility
from .floor_schedule_revision import apply as floor_schedule
from .public_interiors_revision import apply as public_interiors
from .wtc7_interior_revision import apply as wtc7_interior
from .floor_structure_revision import apply as floor_structure


def apply():
    for name,fn in (('paving',paving),('lobby',lobby),('facade',facade),('wtc7_roof',roof7),('crown_junction',crown_junction),('original_junction',original_junction)):
        print('REVISION_START '+name,flush=True)
        fn()
        print('REVISION_DONE '+name,flush=True)
    full_crown_height()
    print('REVISION_START flat_crown',flush=True)
    flat_crown()
    print('REVISION_DONE flat_crown',flush=True)

    oct15()
    south_roof()

    lobby_plan()

    base_frame()
    interior_visibility()
    floor_schedule()
    public_interiors()
    wtc7_interior()
    floor_structure()
