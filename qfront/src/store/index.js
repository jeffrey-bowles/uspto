import Vue from 'vue'
import Vuex from 'vuex'

import savedprops from './savedprops'

Vue.use(Vuex)

export default function (/* { ssrContext } */) {
  const Store = new Vuex.Store({
    modules: {
      // then we reference it
      savedprops
    },

    // enable strict mode (adds overhead!)
    // for dev mode only
    strict: process.env.DEV
  })

  /*
    if we want some HMR magic for it, we handle
    the hot update like below. Notice we guard this
    code with "process.env.DEV" -- so this doesn't
    get into our production build (and it shouldn't).
  */

  if (process.env.DEV && module.hot) {
    module.hot.accept(['./savedprops'], () => {
      const newSavedprops = require('./savedprops').default
      Store.hotUpdate({ modules: { savedprops: newSavedprops } })
    })
  }

  return Store
}