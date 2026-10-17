const MILLENNIUM_IS_CLIENT_MODULE = false;
const pluginName = "luatools";
function InitializePlugins() {
    var _a, _b;
    (_a = (window.PLUGIN_LIST || (window.PLUGIN_LIST = {})))[pluginName] || (_a[pluginName] = {});
    (_b = (window.MILLENNIUM_PLUGIN_SETTINGS_STORE || (window.MILLENNIUM_PLUGIN_SETTINGS_STORE = {})))[pluginName] || (_b[pluginName] = {});
}
InitializePlugins()
const __call_server_method__ = (methodName, kwargs) => Millennium.callServerMethod(pluginName, methodName, kwargs)
const __wrapped_callable__ = (route) => MILLENNIUM_API.callable(__call_server_method__, route)
let PluginEntryPointMain = function() { var millennium_main=function(e){"use strict";return e.default=async function(){},Object.defineProperty(e,"__esModule",{value:!0}),e}({});
 return millennium_main; };
function ExecutePluginModule() {
    let MillenniumStore = window.MILLENNIUM_PLUGIN_SETTINGS_STORE[pluginName];
    function OnPluginConfigChange() {}
    MillenniumStore.OnPluginConfigChange = OnPluginConfigChange;
    let PluginModule = PluginEntryPointMain();
    Object.assign(window.PLUGIN_LIST[pluginName], {
        ...PluginModule,
        __millennium_internal_plugin_name_do_not_use_or_change__: pluginName,
    });
    PluginModule.default();
    if (MILLENNIUM_IS_CLIENT_MODULE) {
        MILLENNIUM_BACKEND_IPC.postMessage(1, { pluginName: pluginName });
    }
}
ExecutePluginModule()

