/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";
import { parseDate, formatDate, serializeDate } from "@web/core/l10n/dates";
const { DateTime } = luxon;

publicWidget.registry.mgsClaimPortal = publicWidget.Widget.extend({
    selector: '#wrapwrap:has(.new_claim_form, .edit_claim_form)',

    events: {
        'click .new_claim_confirm': '_onNewClaimConfirm',
        'click .edit_claim_confirm': '_onEditClaimConfirm',
        'change .policy': '_onChangePolicy',
        'change .member': '_onChangeMember',
        'change .vehicle': '_onChangeVehicle',
        'click .add_claim_line': '_onClickAdd_claim_line',
       	'click .remove_line': '_onClickRemove_line',
       	'click .open_edit_dialog': '_onClickOpenEditiDalog',
       	'change .qty': '_onChangeQtyRate',
       	'change .rate': '_onChangeQtyRate',
       	'change .qty': '_onChangeTotal',
       	'change .rate': '_onChangeTotal',
    },


    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },

     /**
     * @private
     * @param {jQuery} $btn
     * @param {function} callback
     * @returns {Promise}
     */
     _buttonExec: function ($btn, callback) {
        // TODO remove once the automatic system which does this lands in master
        $btn.prop('disabled', true);
        return callback.call(this).catch(function (e) {
            $btn.prop('disabled', false);
            if (e instanceof Error) {
                return Promise.reject(e);
            }
        });
    },

    /**
     * @private
     * @returns {Promise}
     */
    _createClaim: function () {
        var self = this;
        var claim_data = [];
        var rows = $('.claims_table > tbody > tr.claim_cost_line');
        
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            let name = $(row).find('input[name="name"]').val();
            let category = $(row).find('select#category').val();
            let qty = $(row).find('input[name="qty"]').val();
            let rate = $(row).find('input[name="rate"]').val();
            claim_data.push((0, 0, {
                'name': name,
                'health_coverage_type': category,
                'qty': qty,
                'rate': rate
            }));
        }
    
        return this.orm.call("ms_insurance.insurance_claim", "create_claim_portal", [{
            policy: $('.new_claim_form .policy').val(),
            member: $('.new_claim_form .member').val(),
            vehicle: $('.new_claim_form .vehicle').val(),
            lines: claim_data
        }]).then(function (response) {
            if (response.errors) {
                $('#new-claim-dialog .alert').remove();
                $('#new-claim-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                window.location = '/my/claims/';
            }
        });
    },

    _editClaim: function () {
        var self = this;
        var claim_data = [];
        var rows = $('.claims_table > tbody > tr.claim_cost_line');
        
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            let name = $(row).find('input[name="name"]').val();
            let category = $(row).find('select#category').val();
            let qty = $(row).find('input[name="qty"]').val();
            let rate = $(row).find('input[name="rate"]').val();
            claim_data.push((0, 0, {
                'name': name,
                'health_coverage_type': category,
                'qty': qty,
                'rate': rate
            }));
        }

        console.log('----------------------Bd-------------------------------');
    
        return this.orm.call("ms_insurance.insurance_claim", "edit_claim_portal", [{
            claim_id: $('.edit_claim_form .claim_id').val(),
            policy: $('.edit_claim_form .policy').val(),
            member: $('.edit_claim_form .member').val(),
            vehicle: $('.edit_claim_form .vehicle').val(),
            lines: claim_data
        }]).then(function (response) {
            if (!response.claim) {
                $('#new-claim-dialog .alert').remove();
                $('#new-claim-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                window.location.reload();

            }
        });
    },
    
    _onClickOpenEditiDalog: function (ev) {
        this._onChangePolicy();
        this._onChangeMember();
        this._onChangeVehicle();
        this._onChangeTotal();
    },

    _onNewClaimConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._buttonExec($(ev.currentTarget), this._createClaim);
    },

    _onEditClaimConfirm: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        this._buttonExec($(ev.currentTarget), this._editClaim);
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangePolicy: function (ev) {
        const policy = this.el.querySelector('.policy').value.trim();

        if (!policy){
            return
        }
        let cust_nameEl = this.el.querySelector('.cust_name');
        let cust_genderEl = this.el.querySelector('.cust_gender');
        let cust_mobileEl = this.el.querySelector('.cust_mobile');

        this.orm.call("ms_insurance.insurance_claim", "get_policy_info", [
            policy
        ]).then(function (response) {
            if (response.errors) {
                $('#new-claim-dialog .alert').remove();
                $('#new-claim-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                cust_nameEl.innerText  = 'Customer Name: ' + response.cust_name;
                cust_genderEl.innerText  = 'Gender: ' + response.cust_gender;
                cust_mobileEl.innerText  = 'Mobile: ' + response.cust_mobile;
            }
        });
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeMember: function (ev) {

        let member =this.el.querySelector('.member');
        if (!member){
            return
        }
        member  = member.value.trim();
        if (!member){
            return
        }
        let member_nameEl = this.el.querySelector('.member_name');
        let member_genderEl = this.el.querySelector('.member_gender');
        let member_mobileEl = this.el.querySelector('.member_mobile');
        let member_imageEl = this.el.querySelector('.member_image');
        let member_dobEl = this.el.querySelector('.member_dob');
        let member_ageEl = this.el.querySelector('.member_age');
        let member_blood_groupEl = this.el.querySelector('.member_blood_group');

        this.orm.call("ms_insurance.insurance_claim", "get_member_info", [
            member
        ]).then(function (response) {
            if (response.errors) {
                $('#new-claim-dialog .alert').remove();
                $('#new-claim-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                member_imageEl.setAttribute("src", "data:image/png;base64," + response.cust_image);
                member_nameEl.innerText  = 'Customer Name: ' + (response.cust_name ? response.cust_name : '');
                member_genderEl.innerText  = 'Gender: ' + (response.cust_gender ? response.cust_gender : '');
                member_mobileEl.innerText  = 'Mobile: ' + (response.cust_mobile ? response.cust_mobile : '');
                member_dobEl.innerText  = 'DOB: ' + (response.cust_dob ? response.cust_dob : '');
                member_ageEl.innerText  = 'Age: ' + (response.age ? response.age : '');
                member_blood_groupEl.innerText  = 'Blood Group: ' + (response.blood_group ? response.blood_group : '');

            }
        });
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeVehicle: function (ev) {
        let vehicle = this.el.querySelector('.vehicle')
        if (!vehicle){
            return
        }
        vehicle = vehicle.value.trim();
        let vehicle_noEl = this.el.querySelector('.vehicle_no');
        let vehicle_model_yearEl = this.el.querySelector('.vehicle_model_year');
        let vehicle_transmissionEl = this.el.querySelector('.vehicle_transmission');
        let vehicle_imageEl = this.el.querySelector('.vehicle_image');
        let vehicle_fuel_typeEl = this.el.querySelector('.vehicle_fuel_type');
        let vehicle_horsepowerEl = this.el.querySelector('.vehicle_horsepower');

        this.orm.call("ms_insurance.insurance_claim", "get_vehicle_info", [
            vehicle
        ]).then(function (response) {
            if (response.errors) {
                $('#new-claim-dialog .alert').remove();
                $('#new-claim-dialog div:first').prepend('<div class="alert alert-danger">' + response.errors + '</div>');
                return Promise.reject(response);
            } else {
                vehicle_imageEl.setAttribute("src", "data:image/png;base64," + response.image_128);
                vehicle_noEl.innerText  = 'Vehicle#: ' + (response.name ? response.name : '');
                vehicle_model_yearEl.innerText  = 'Year: ' + (response.model_year ? response.model_year : '');
                vehicle_transmissionEl.innerText  = 'Transmission: ' + (response.transmission ? response.transmission : '');
                vehicle_fuel_typeEl.innerText  = 'Fuel Type: ' + (response.fuel_type ? response.fuel_type : '');
                vehicle_horsepowerEl.innerText  = 'Horsepower: ' + (response.horsepower ? response.horsepower : '');

            }
        });
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onChangeTotal: function (ev) {
        var rows = document.getElementsByClassName('claim_cost_line');
        let total = 0;
    
        // Loop through each row
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            let totalEl = row.querySelector('.total');
            
            // Find the input elements for quantity and rate in this row
            var qtyInput = row.querySelector('input[name="qty"]');
            var rateInput = row.querySelector('input[name="rate"]');
            
            // Get the values of the inputs
            var qty = parseFloat(qtyInput.value);
            var rate = parseFloat(rateInput.value);

            let subtotal = qty * rate;
            if (qtyInput && rateInput) {
                totalEl.innerText = subtotal.toLocaleString(); // Add comma separator
            }
            
            // Calculate and accumulate the total
            total += subtotal;
        }
    
        // Update the total element
        var totalElement = document.querySelector('.total_claimed');
        totalElement.textContent = total.toFixed(2); 
    },
    


    /**
     * @private
     * @param {Event} ev
     */
    _onChangeQtyRate: function (ev) {
        const qty = ev.currentTarget.value.trim();
        let parentRow = ev.currentTarget.closest('.claim_cost_line');
        let qtyEl = parentRow.querySelector('.qty');
        let rateEl = parentRow.querySelector('.rate');
        let totalEl = parentRow.querySelector('.total');
        let total = qtyEl.value * rateEl.value;
        if (qtyEl && rateEl) {
            totalEl.innerText = total.toLocaleString(); // Add comma separator
        }
    },

    _onClickRemove_line: function(ev) {
        $(ev.currentTarget).closest('.claim_cost_line').remove();
    },

    _onClickAdd_claim_line: function(ev){
        var $new_row = $('.add_extra_claim').clone(true);
        $new_row.removeClass('d-none');
        $new_row.removeClass('add_extra_claim');
        $new_row.addClass('claim_cost_line');
        $new_row.insertBefore($('.add_extra_claim'));
        // _.each($new_row.find('td'), function(val) {
        //     $(val).find('input').attr('required', 'required');
        // });
    },

//     _onClickSubmit: async function(ev){
//         var self = this;
//         var claim_data = [];
//         var rows = $('.claims_table > tbody > tr.claim_cost_line');
//         _.each(rows, function(row) {
//             let name = $(row).find('input[name="name"]').val();
//             let category = $(row).find('select#category').val();
//             let qty = $(row).find('input[name="qty"]').val();
//             let rate = $(row).find('input[name="rate"]').val();
//             claim_data.push({
//                 'name': name,
//                 'category': category,
//                 'qty': qty,
//                 'rate': rate,
//             });
//         });
//         $('textarea[name="data_line_ids"]').val(JSON.stringify(claim_data));

//    },
})