from backports.datetime_fromisoformat import MonkeyPatch
import nwhl_lib

MonkeyPatch.patch_fromisoformat()
print(nwhl_lib.exec_get_func("https://web.api.digitalshift.ca/partials/stats/schedule/table?division_id=13893&all"))
