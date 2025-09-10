1. cant select the pump number in pump control component on hardware testing page
2. connected small card in top right corner says "object Object" instead of connected/disconnected
3. Under nutrient page, this value isnt displaying  in the Current Mix card towards the top 
Current Mix
Total: () => { return Object.values($.get(dispenseAmounts)).reduce((sum, vol) => sum + vol, 0); }ml
() => { return Object.entries($.get(dispenseAmounts)).filter(([id, amount]) => amount > 0).map(([id, amount]) => `${amount}ml ${pumpNames[id]}`).join(', '); }
4. I just calibrated the atlas scientific EZO peristaltic pumps for nutes but the system doesnt recognize their calibration status
5. cant access the settings page, get this error in the console:
Settings.svelte:77  GET http://localhost:5173/api/settings/user 404 (NOT FOUND)
loadSettings @ Settings.svelte:77
untrack @ chunk-GDZTTDT7.js?v=7e5ee1b4:3294
$effect @ chunk-VSV43TSV.js?v=7e5ee1b4:3287
update_reaction @ chunk-GDZTTDT7.js?v=7e5ee1b4:3007
update_effect @ chunk-GDZTTDT7.js?v=7e5ee1b4:3137
flush_queued_effects @ chunk-GDZTTDT7.js?v=7e5ee1b4:2308
process @ chunk-GDZTTDT7.js?v=7e5ee1b4:2020
flush_effects @ chunk-GDZTTDT7.js?v=7e5ee1b4:2280
flush @ chunk-GDZTTDT7.js?v=7e5ee1b4:2080
(anonymous) @ chunk-GDZTTDT7.js?v=7e5ee1b4:2129
dequeue @ chunk-GDZTTDT7.js?v=7e5ee1b4:1891
Settings.svelte:78  GET http://localhost:5173/api/settings/developer 404 (NOT FOUND)
loadSettings @ Settings.svelte:78
untrack @ chunk-GDZTTDT7.js?v=7e5ee1b4:3294
$effect @ chunk-VSV43TSV.js?v=7e5ee1b4:3287
update_reaction @ chunk-GDZTTDT7.js?v=7e5ee1b4:3007
update_effect @ chunk-GDZTTDT7.js?v=7e5ee1b4:3137
flush_queued_effects @ chunk-GDZTTDT7.js?v=7e5ee1b4:2308
process @ chunk-GDZTTDT7.js?v=7e5ee1b4:2020
flush_effects @ chunk-GDZTTDT7.js?v=7e5ee1b4:2280
flush @ chunk-GDZTTDT7.js?v=7e5ee1b4:2080
(anonymous) @ chunk-GDZTTDT7.js?v=7e5ee1b4:2129
dequeue @ chunk-GDZTTDT7.js?v=7e5ee1b4:1891
chunk-GDZTTDT7.js?v=7e5ee1b4:382 Uncaught Svelte error: props_invalid_value
Cannot do `bind:value={undefined}` when `value` has a fallback value
https://svelte.dev/e/props_invalid_value

	in <unknown>
	in TabsRoot.svelte
	in Settings.svelte
	in SidebarInset.svelte
	in Sidebar.svelte
	in dashboard-layout.svelte
	in App.svelte