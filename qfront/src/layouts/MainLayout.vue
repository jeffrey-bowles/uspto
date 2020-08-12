<template>
  <q-layout view="hHh lpR fFf">
    <q-header reveal elevated class="bg-primary text-white glossy">
      <q-tabs v-model="tab" align="center" narrow-indicator class="grey-3" dense>
        <q-route-tab name="fee1" to="/fee/1" label="3.5 years"/>
        <q-route-tab name="fee2" to="/fee/2" label="3.5 years (surcharge)"/>
        <q-route-tab name="fee3" to="/fee/3" label="7.5 years"/>
        <q-route-tab name="fee4" to="/fee/4" label="7.5 years (surcharge)"/>
        <q-route-tab name="fee5" to="/fee/5" label="11.5 years"/>
        <q-route-tab name="fee6" to="/fee/6" label="11.5 years (surcharge)"/>
      </q-tabs>
    </q-header>

    <q-tab-panels v-model="tab" keep-alive>
      <q-tab-panel name="fee1">
        <router-view/>
      </q-tab-panel>
      <q-tab-panel name="fee2">
        <router-view/>
      </q-tab-panel>
      <q-tab-panel name="fee3">
        <router-view/>
      </q-tab-panel>
      <q-tab-panel name="fee4">
        <router-view/>
      </q-tab-panel>
      <q-tab-panel name="fee5">
        <router-view/>
      </q-tab-panel>
      <q-tab-panel name="fee6">
        <router-view/>
      </q-tab-panel>
    </q-tab-panels>

  </q-layout>
</template>

<script>
export default {
  name: 'MainLayout',
  data() {
    return {
      tab: 'fee1'
    }
  }
}
</script>
