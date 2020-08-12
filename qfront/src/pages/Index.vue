<template>
  <div class="q-pa-md">
    <q-table
      title="Patent Documents"
      class="my-sticky-header-table"
      :data="data"
      :columns="columns"
      row-key="id"
      :pagination.sync="pagination"
      :loading="loading"
      :filter="filter"
      :rows-per-page-options="[50, 100, 500, 1000, 2500, 5000, 10000, 0]"
      @request="onRequest"
      binary-state-sort
    >

      <template v-slot:top-right>
        <div class="q-ml-xl">
          <q-btn
            color="primary"
            icon-right="archive"
            label="Export to csv"
            no-caps
            @click="exportTable"
          />
        </div>
        <div class="q-ml-xl">
          <q-checkbox v-model="only_unpaid" label="Show unpaid only"
          v-on:click.native="onlyUnpaid" />
        </div>
        <div class="q-ml-xl">
          <q-input dense debounce="300" v-model="filter" placeholder="Search">
            <template v-slot:append>
              <q-icon name="search"></q-icon>
            </template>
          </q-input>
        </div>
        <div class="q-ml-xl">
          <q-btn
            flat round dense
            @click="toggle"
            :icon="$q.fullscreen.isActive ? 'fullscreen_exit' : 'fullscreen'"
            :label="$q.fullscreen.isActive ? 'Exit Fullscreen' : 'Go Fullscreen'"
            class="q-ml-md"
          />
        </div>
      </template>

      <template v-slot:header="props">
        <q-tr :props="props">
          <q-th auto-width>
            Fee History
          </q-th>
          <q-th
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
          >
            {{ col.label }}
          </q-th>
        </q-tr>
      </template>

      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td auto-width>
            <q-btn size="sm" color="primary" round dense
            @click="props.expand = !props.expand; props.expand ?
            getFeeEvents(props.row.id) : getFeeEvents('close')"
            :icon="props.expand ? 'remove' : 'add'" />
          </q-td>
          <q-td
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
          >
            {{ col.value }}
          </q-td>
        </q-tr>
        <q-tr v-show="props.expand" :id="'expanded_'+props.row.id"
        :props="props">
          <q-td colspan="100%">
          </q-td>
        </q-tr>
      </template>
      <template v-slot:loading>
        <q-inner-loading showing color="primary" />
      </template>
    </q-table>
  </div>
</template>

<script>
import { axiosInstance } from 'boot/axios'
import {
  exportFile
} from 'quasar'

function wrapCsvValue (val, formatFn) {
  let formatted = formatFn !== void 0
    ? formatFn(val)
    : val

  formatted = formatted === void 0 || formatted === null
    ? ''
    : String(formatted)

  formatted = formatted.split('"').join('""')

  return `"${formatted}"`
}

export default {
  name: 'PageIndex',
  data () {
    return {
      only_unpaid: false,
      filter: '',
      loading: false,
      pagination: {
        sortBy: 'patent_number',
        descending: false,
        page: 1,
        rowsPerPage: 50,
        rowsNumber: 100
      },
      columns: [
        {
          name: 'patent_number',
          required: true,
          label: 'Patent Number',
          align: 'left',
          field: row => row.patent_number,
          sortable: true
        }, {
          name: 'issue_date',
          align: 'left',
          label: 'Issue Date',
          field: 'issue_date',
          sortable: true
        }, {
          name: 'application_number',
          align: 'left',
          label: 'Application Number',
          field: 'application_number',
          sortable: true
        }, {
          name: 'application_date',
          align: 'left',
          label: 'Application Date',
          field: 'application_date',
          sortable: true
        }, {
          name: 'pat_assignee_name',
          align: 'left',
          label: 'Assignee',
          field: 'pat_assignee_name',
          sortable: true
        }, {
          name: 'pat_assignee_address',
          align: 'left',
          label: 'Assignee Address',
          field: 'pat_assignee_address',
          sortable: false
        }, {
          name: 'correspondent_name',
          align: 'left',
          label: 'Correspondent',
          field: 'correspondent_name',
          sortable: true
        }, {
          name: 'correspondent_address',
          align: 'left',
          label: 'Correspondent Address',
          field: 'correspondent_address',
          sortable: false
        }, {
          name: 'entity_status',
          align: 'center',
          label: 'Entity Status',
          field: 'entity_status',
          sortable: false
        }
      ],
      data: []
    }
  },
  mounted () {
    this.onRequest({
      pagination: this.pagination,
      filter: undefined
    })
  },
  methods: {
    onRequest (props) {
      const {
        page,
        rowsPerPage,
        sortBy,
        descending
      } = props.pagination
      const filter = props.filter
      const unpaid = this.only_unpaid

      // change state to loading
      this.loading = true

      // number of rows to get
      const fetchCount = rowsPerPage === 0 ?
      this.pagination.rowsNumber : rowsPerPage

      // calculate starting row of data
      const startRow = (page - 1) * rowsPerPage

      // fetch data from "server"
      this.fetchFromServer(
        startRow, fetchCount, filter, sortBy, descending, unpaid
      )
      // update local pagination object
      this.pagination.page = page
      this.pagination.rowsPerPage = rowsPerPage
      this.pagination.sortBy = sortBy
      this.pagination.descending = descending
    },
    
    // This is identical to onRequest with the exception that it doesn't use
    // the props, since none of the table variables have changed
    onlyUnpaid () {
      const {
        page,
        rowsPerPage,
        sortBy,
        descending
      } = this.pagination

      this.loading = true
      const filter = this.filter
      const unpaid = this.only_unpaid
      const fetchCount = rowsPerPage === 0 ?
      this.pagination.rowsNumber : rowsPerPage
      const startRow = (page - 1) * rowsPerPage
      this.fetchFromServer(
        startRow, fetchCount, filter, sortBy, descending, unpaid
      )
    },

    // fetch requested rows using Vue.js/quasar framework
    fetchFromServer (startRow, count, filter, sortBy, descending, unpaid) {
      // Need to get Route id to determine which maintenance fee set to load
      var patentSet = '1'
      if (this.$route.params.id !== undefined) {
        patentSet = String(this.$route.params.id)
      }
      axiosInstance.request({
        method: 'GET',
        url: 'api/update_patents',
        params: {
          patent_set: patentSet,
          start_row: startRow,
          count: count,
          filter: filter,
          sort_by: sortBy,
          descending: descending,
          unpaid: unpaid
        }
      })
      .then(response => {
        // update rows and pagination data
        this.data = response.data.patents
        this.pagination.rowsNumber = response.data.count
        this.loading = false
      })
      .catch((err) => {
        console.error(err)
      })
    },

    // toggle fullscreen mode
    toggle (e) {
      const target = e.target.parentNode.parentNode.parentNode.parentNode
      .parentNode.parentNode.parentNode
      this.$q.fullscreen.toggle(target)
      .then(() => {
      })
      .catch((err) => {
        console.error(err)
      })
    },

    // Get Maintenance Fee Event information using django framework
    getFeeEvents (patentNumber) {
      const patentString = String(patentNumber)
      const target = document.getElementById('expanded_'+patentString)
      //  DOUBLE CHECK THIS IF STATEMENT
      if (patentString != 'close') {
        axiosInstance.request({
          method: 'GET',
          url: 'api/update_fee_events',
          params: {
            patent: patentString,
          }
        })
        .then(response => {
          target.firstElementChild.innerHTML = response.data
        })
        .catch((err) => {
          console.error(err)
        })
      }
    },

    // include quasar exportTable functionality
    exportTable () {
      const content = [this.columns.map(col => wrapCsvValue(col.label))].concat(
        this.data.map(row => this.columns.map(col => wrapCsvValue(
          typeof col.field === 'function'
            ? col.field(row)
            : row[col.field === void 0 ? col.name : col.field],
          col.format
        )).join(','))
      ).join('\r\n')

      const status = exportFile(
        'table-export.csv',
        content,
        'text/csv'
      )

      if (status !== true) {
        this.$q.notify({
          message: 'Browser denied file download...',
          color: 'negative',
          icon: 'warning'
        })
      }
    }
  }
}
</script>
