function storePageInfo() {{
    pycmd("store")
}}

function restoreScroll() {{
    window.scrollTo(0, {savedPos});
}}

onUpdateHook.push(storePageInfo);
onUpdateHook.push(restoreScroll);
