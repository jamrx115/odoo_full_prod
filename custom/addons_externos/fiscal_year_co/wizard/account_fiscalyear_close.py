# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp



class account_move_line(osv.osv):
    _inherit = "account.move.line"

    def _query_get_v8(self, cr, uid, obj='l', context=None):
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalperiod_obj = self.pool.get('account.period')
        account_obj = self.pool.get('account.account')
        fiscalyear_ids = []
        context = dict(context or {})
        initial_bal = context.get('initial_bal', False)
        company_clause = " "
        query = ''
        query_params = {}
        if context.get('company_id'):
            company_clause = " AND " +obj+".company_id = %(company_id)s"
            query_params['company_id'] = context['company_id']
        if not context.get('fiscalyear'):
            if context.get('all_fiscalyear'):
                #this option is needed by the aged balance report because otherwise, if we search only the draft ones, an open invoice of a closed fiscalyear won't be displayed
                fiscalyear_ids = fiscalyear_obj.search(cr, uid, [])
            else:
                #fiscalyear_ids = fiscalyear_obj.search(cr, uid, [('state', '=', 'draft')])
                fiscalyear_ids = fiscalyear_obj.search(cr, uid, [])
        else:
            #for initial balance as well as for normal query, we check only the selected FY because the best practice is to generate the FY opening entries
            fiscalyear_ids = context['fiscalyear']
            if isinstance(context['fiscalyear'], (int, long)):
                fiscalyear_ids = [fiscalyear_ids]

        query_params['fiscalyear_ids'] = tuple(fiscalyear_ids) or (0,)
        state = context.get('state', False)
        where_move_state = ''
        where_move_lines_by_date = ''

        if context.get('date_from') and context.get('date_to'):
            query_params['date_from'] = context['date_from']
            query_params['date_to'] = context['date_to']
            if initial_bal:
                where_move_lines_by_date = " AND " +obj+".move_id IN (SELECT id FROM account_move WHERE date < %(date_from)s)"
            else:
                where_move_lines_by_date = " AND " +obj+".move_id IN (SELECT id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s)"

        if state:
            if state.lower() not in ['all']:
                query_params['state'] = state
                where_move_state= " AND "+obj+".move_id IN (SELECT id FROM account_move WHERE account_move.state = %(state)s)"
        if context.get('period_from') and context.get('period_to') and not context.get('periods'):
            if initial_bal:
                period_company_id = fiscalperiod_obj.browse(cr, uid, context['period_from'], context=context).company_id.id
                first_period = fiscalperiod_obj.search(cr, uid, [('company_id', '=', period_company_id)], order='date_start', limit=1)[0]
                context['periods'] = fiscalperiod_obj.build_ctx_periods(cr, uid, first_period, context['period_from'])
            else:
                context['periods'] = fiscalperiod_obj.build_ctx_periods(cr, uid, context['period_from'], context['period_to'])
        if context.get('periods'):
            query_params['period_ids'] = tuple(context['periods'])
            if initial_bal:
                query = obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN %(fiscalyear_ids)s)" + where_move_state + where_move_lines_by_date
                period_ids = fiscalperiod_obj.search(cr, uid, [('id', 'in', context['periods'])], order='date_start', limit=1)
                if period_ids and period_ids[0]:
                    first_period = fiscalperiod_obj.browse(cr, uid, period_ids[0], context=context)
                    query_params['date_start'] = first_period.date_start
                    query = obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN %(fiscalyear_ids)s AND date_start <= %(date_start)s AND id NOT IN %(period_ids)s)" + where_move_state + where_move_lines_by_date
            else:
                query = obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN %(fiscalyear_ids)s AND id IN %(period_ids)s)" + where_move_state + where_move_lines_by_date
        else:
            query = obj+".period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN %(fiscalyear_ids)s)" + where_move_state + where_move_lines_by_date

        if initial_bal and not context.get('periods') and not where_move_lines_by_date:
            #we didn't pass any filter in the context, and the initial balance can't be computed using only the fiscalyear otherwise entries will be summed twice
            #so we have to invalidate this query
            raise osv.except_osv(_('Warning!'),_("You have not supplied enough arguments to compute the initial balance, please select a period and a journal in the context."))

        if context.get('journal_ids'):
            query_params['journal_ids'] = tuple(context['journal_ids'])
            query += ' AND '+obj+'.journal_id IN %(journal_ids)s'

        if context.get('chart_account_id'):
            child_ids = account_obj._get_children_and_consol(cr, uid, [context['chart_account_id']], context=context)
            query_params['child_ids'] = tuple(child_ids)
            query += ' AND '+obj+'.account_id IN %(child_ids)s'

        query += company_clause
        return cr.mogrify(query, query_params)


class account_account(osv.osv):
    _inherit = "account.account"

    def _get_children_and_consol(self, cr, uid, ids, context=None):
        #this function search for all the children and all consolidated children (recursively) of the given account ids
        ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)], context=context)
        ids3 = []
        for rec in self.browse(cr, uid, ids2, context=context):
            for child in rec.child_consol_ids:
                ids3.append(child.id)
        if ids3:
            ids3 = self._get_children_and_consol(cr, uid, ids3, context)
        return ids2 + ids3

    def _get_child_ids(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.child_parent_ids:
                result[record.id] = [x.id for x in record.child_parent_ids]
            else:
                result[record.id] = []

            if record.child_consol_ids:
                for acc in record.child_consol_ids:
                    if acc.id not in result[record.id]:
                        result[record.id].append(acc.id)

        return result

    def __compute(self, cr, uid, ids, field_names, arg=None, context=None,
                  query='', query_params=()):
        """ compute the balance, debit and/or credit for the provided
        account ids
        Arguments:
        `ids`: account ids
        `field_names`: the fields to compute (a list of any of
                       'balance', 'debit' and 'credit')
        `arg`: unused fields.function stuff
        `query`: additional query filter (as a string)
        `query_params`: parameters for the provided query string
                        (__compute will handle their escaping) as a
                        tuple
        """
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit",
            # by convention, foreign_balance is 0 when the account has no secondary currency, because the amounts may be in different currencies
            'foreign_balance': "(SELECT CASE WHEN currency_id IS NULL THEN 0 ELSE COALESCE(SUM(l.amount_currency), 0) END FROM account_account WHERE id IN (l.account_id)) as foreign_balance",
        }
        #get all the necessary accounts
        children_and_consolidated = self._get_children_and_consol(cr, uid, ids, context=context)
        #compute for each account the balance/debit/credit from the move lines
        accounts = {}
        res = {}
        null_result = dict((fn, 0.0) for fn in field_names)
        if children_and_consolidated:
            aml_query = self.pool.get('account.move.line')._query_get_v8(cr, uid, context=context)

            wheres = [""]
            if query.strip():
                wheres.append(query.strip())
            if aml_query.strip():
                wheres.append(aml_query.strip())
            filters = " AND ".join(wheres)
            # IN might not work ideally in case there are too many
            # children_and_consolidated, in that case join on a
            # values() e.g.:
            # SELECT l.account_id as id FROM account_move_line l
            # INNER JOIN (VALUES (id1), (id2), (id3), ...) AS tmp (id)
            # ON l.account_id = tmp.id
            # or make _get_children_and_consol return a query and join on that
            request = ("SELECT l.account_id as id, " +\
                       ', '.join(mapping.values()) +
                       " FROM account_move_line l" \
                       " WHERE l.account_id IN %s " \
                            + filters +
                       " GROUP BY l.account_id")
            params = (tuple(children_and_consolidated),) + query_params
            cr.execute(request, params)

            for row in cr.dictfetchall():
                accounts[row['id']] = row

            # consolidate accounts with direct children
            children_and_consolidated.reverse()
            brs = list(self.browse(cr, uid, children_and_consolidated, context=context))
            sums = {}
            currency_obj = self.pool.get('res.currency')
            while brs:
                current = brs.pop(0)
                for fn in field_names:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
                    for child in current.child_id:
                        if child.company_id.currency_id.id == current.company_id.currency_id.id:
                            sums[current.id][fn] += sums[child.id][fn]
                        else:
                            sums[current.id][fn] += currency_obj.compute(cr, uid, child.company_id.currency_id.id, current.company_id.currency_id.id, sums[child.id][fn], context=context)

                # as we have to relay on values computed before this is calculated separately than previous fields
                if current.currency_id and current.exchange_rate and \
                            ('adjusted_balance' in field_names or 'unrealized_gain_loss' in field_names):
                    # Computing Adjusted Balance and Unrealized Gains and losses
                    # Adjusted Balance = Foreign Balance / Exchange Rate
                    # Unrealized Gains and losses = Adjusted Balance - Balance
                    adj_bal = sums[current.id].get('foreign_balance', 0.0) / current.exchange_rate
                    sums[current.id].update({'adjusted_balance': adj_bal, 'unrealized_gain_loss': adj_bal - sums[current.id].get('balance', 0.0)})

            for id in ids:
                res[id] = sums.get(id, null_result)
        else:
            for id in ids:
                res[id] = null_result
        return res

    _columns = {
        'balance': fields.function(__compute, digits_compute=dp.get_precision('Account'), string='Balance', multi='balance'),
        'child_consol_ids': fields.many2many('account.account', 'account_account_consol_rel', 'child_id', 'parent_id', 'Consolidated Children'),
        'child_id': fields.function(_get_child_ids, type='many2many', relation="account.account", string="Child Accounts"),
    }


class account_fiscalyear_close(osv.osv_memory):
    """
    Closes Account Fiscalyear and Generate Opening entries for New Fiscalyear
    """
    _name = "account.fiscalyear.close"
    _description = "Fiscalyear Close"
    _columns = {
       'fy_id': fields.many2one('account.fiscalyear', \
                                 'Fiscal Year to close', required=True, help="Select a Fiscal year to close"),
       'fy2_id': fields.many2one('account.fiscalyear', \
                                 'New Fiscal Year', required=True),
       'journal_id': fields.many2one('account.journal', 'Opening Entries Journal', domain="[('type','=','general')]", required=True, help='The best practice here is to use a journal dedicated to contain the opening entries of all fiscal years. Note that you should define it with default debit/credit accounts, of type \'situation\' and with a centralized counterpart.'),
       'period_id': fields.many2one('account.period', 'Opening Entries Period', required=True),
       'report_name': fields.char('Name of new entries', required=True, help="Give name of the new entries"),
    }
    _defaults = {
        'report_name': lambda self, cr, uid, context: _('End of Fiscal Year Entry'),
    }

    def data_save(self, cr, uid, ids, context=None):
        """
        This function close account fiscalyear and create entries in new fiscalyear
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Account fiscalyear close state’s IDs

        """
        def _reconcile_fy_closing(cr, uid, ids, context=None):
            """
            This private function manually do the reconciliation on the account_move_line given as `ids´, and directly
            through psql. It's necessary to do it this way because the usual `reconcile()´ function on account.move.line
            object is really resource greedy (not supposed to work on reconciliation between thousands of records) and
            it does a lot of different computation that are useless in this particular case.
            """
            #check that the reconcilation concern journal entries from only one company
            cr.execute('select distinct(company_id) from account_move_line where id in %s',(tuple(ids),))
            if len(cr.fetchall()) > 1:
                raise osv.except_osv(_('Warning!'), _('The entries to reconcile should belong to the same company.'))
            r_id = self.pool.get('account.full.reconcile').create(cr, uid, {'type': 'auto', 'opening_reconciliation': True})
            cr.execute('update account_move_line set full_reconcile_id = %s where id in %s',(r_id, tuple(ids),))
            # reconcile_ref deptends from reconcile_id but was not recomputed
            #obj_acc_move_line._store_set_values(cr, uid, ids, ['reconciled'], context=context)
            obj_acc_move_line.invalidate_cache(cr, uid, ['full_reconcile_id'], ids, context=context)
            return r_id

        obj_acc_period = self.pool.get('account.period')
        obj_acc_fiscalyear = self.pool.get('account.fiscalyear')
        obj_acc_journal = self.pool.get('account.journal')
        obj_acc_move = self.pool.get('account.move')
        obj_acc_move_line = self.pool.get('account.move.line')
        obj_acc_account = self.pool.get('account.account')
        obj_acc_journal_period = self.pool.get('account.journal.period')
        currency_obj = self.pool.get('res.currency')

        data = self.browse(cr, uid, ids, context=context)

        if context is None:
            context = {}
        fy_id = data[0].fy_id.id

        cr.execute("SELECT id FROM account_period WHERE date_stop < (SELECT date_start FROM account_fiscalyear WHERE id = %s)", (str(data[0].fy2_id.id),))
        fy_period_set = ','.join(map(lambda id: str(id[0]), cr.fetchall()))
        cr.execute("SELECT id FROM account_period WHERE date_start > (SELECT date_stop FROM account_fiscalyear WHERE id = %s)", (str(fy_id),))
        fy2_period_set = ','.join(map(lambda id: str(id[0]), cr.fetchall()))

        if not fy_period_set or not fy2_period_set:
            raise osv.except_osv(_('User Error!'), _('The periods to generate opening entries cannot be found.'))

        period = obj_acc_period.browse(cr, uid, data[0].period_id.id, context=context)
        new_fyear = obj_acc_fiscalyear.browse(cr, uid, data[0].fy2_id.id, context=context)
        old_fyear = obj_acc_fiscalyear.browse(cr, uid, fy_id, context=context)

        new_journal = data[0].journal_id.id
        new_journal = obj_acc_journal.browse(cr, uid, new_journal, context=context)
        company_id = new_journal.company_id.id

        if not new_journal.default_credit_account_id or not new_journal.default_debit_account_id:
            raise osv.except_osv(_('User Error!'),
                    _('The journal must have default credit and debit account.'))
        #if (not new_journal.centralisation) or new_journal.entry_posted:
        #    raise osv.except_osv(_('User Error!'),
        #            _('The journal must have centralized counterpart without the Skipping draft state option checked.'))

        #delete existing move and move lines if any
        move_ids = obj_acc_move.search(cr, uid, [
            ('journal_id', '=', new_journal.id), ('period_id', '=', period.id)])
        if move_ids:
            move_line_ids = obj_acc_move_line.search(cr, uid, [('move_id', 'in', move_ids)])
            obj_acc_move_line._remove_move_reconcile(cr, uid, move_line_ids, opening_reconciliation=True, context=context)
            obj_acc_move_line.unlink(cr, uid, move_line_ids, context=context)
            obj_acc_move.unlink(cr, uid, move_ids, context=context)

        cr.execute("SELECT id FROM account_fiscalyear WHERE date_stop < %s", (str(new_fyear.date_start),))
        result = cr.dictfetchall()
        fy_ids = [x['id'] for x in result]
        #query_line = obj_acc_move_line._query_get(cr, uid,
        #        obj='account_move_line', context={'fiscalyear': fy_ids})

        query_line = "account_move_line.period_id IN (SELECT id FROM account_period WHERE fiscalyear_id IN (SELECT id FROM account_fiscalyear WHERE date_stop < '" + str(new_fyear.date_start)+ "'))"

        #create the opening move
        vals = {
            'name': '/',
            'ref': '',
            'period_id': period.id,
            'date': period.date_start,
            'journal_id': new_journal.id,
        }
        move_id = obj_acc_move.create(cr, uid, vals, context=context)

        #1. report of the accounts with defferal method == 'unreconciled'
        cr.execute('''
            SELECT a.id
            FROM account_account a
            LEFT JOIN account_account_type t ON (a.user_type_id = t.id)
            WHERE NOT a.deprecated
              AND a.internal_type not in ('view', 'consolidation')
              AND a.company_id = %s
              AND t.close_method = %s''', (company_id, 'unreconciled', ))
        account_ids = map(lambda x: x[0], cr.fetchall())
        if account_ids:
            cr.execute('''
                INSERT INTO account_move_line (
                     name, create_uid, create_date, write_uid, write_date,
                     statement_id, journal_id, currency_id, date_maturity,
                     partner_id, blocked, credit, debit,
                     ref, account_id, period_id, date, move_id, amount_currency,
                     quantity, product_id, company_id)
                  (SELECT name, create_uid, create_date, write_uid, write_date,
                     statement_id, %s,currency_id, date_maturity, partner_id,
                     blocked, credit, debit, ref, account_id,
                     %s, (%s) AS date, %s, amount_currency, quantity, product_id, company_id
                   FROM account_move_line
                   WHERE account_id IN %s
                     AND ''' + query_line + '''
                     AND full_reconcile_id IS NULL)''', (new_journal.id, period.id, period.date_start, move_id, tuple(account_ids),))

            #We have also to consider all move_lines that were reconciled
            #on another fiscal year, and report them too
            cr.execute('''
                INSERT INTO account_move_line (
                     name, create_uid, create_date, write_uid, write_date,
                     statement_id, journal_id, currency_id, date_maturity,
                     partner_id, blocked, credit, debit,
                     ref, account_id, period_id, date, move_id, amount_currency,
                     quantity, product_id, company_id)
                  (SELECT
                     b.name, b.create_uid, b.create_date, b.write_uid, b.write_date,
                     b.statement_id, %s, b.currency_id, b.date_maturity,
                     b.partner_id, b.blocked, b.credit, b.debit,
                     b.ref, b.account_id, %s, (%s) AS date, %s, b.amount_currency,
                     b.quantity, b.product_id, b.company_id
                     FROM account_move_line b
                     WHERE b.account_id IN %s
                       AND b.full_reconcile_id IS NOT NULL
                       AND b.period_id IN ('''+fy_period_set+''')
                       AND b.full_reconcile_id IN (SELECT DISTINCT(full_reconcile_id)
                                          FROM account_move_line a
                                          WHERE a.period_id IN ('''+fy2_period_set+''')))''', (new_journal.id, period.id, period.date_start, move_id, tuple(account_ids),))
            self.invalidate_cache(cr, uid, context=context)

        #2. report of the accounts with defferal method == 'detail'
        cr.execute('''
            SELECT a.id
            FROM account_account a
            LEFT JOIN account_account_type t ON (a.user_type_id = t.id)
            WHERE NOT a.deprecated
              AND a.internal_type not in ('view', 'consolidation')
              AND a.company_id = %s
              AND t.close_method = %s''', (company_id, 'detail', ))
        account_ids = map(lambda x: x[0], cr.fetchall())

        if account_ids:
            cr.execute('''
                INSERT INTO account_move_line (
                     name, create_uid, create_date, write_uid, write_date,
                     statement_id, journal_id, currency_id, date_maturity,
                     partner_id, blocked, credit, debit,
                     ref, account_id, period_id, date, move_id, amount_currency,
                     quantity, product_id, company_id)
                  (SELECT name, create_uid, create_date, write_uid, write_date,
                     statement_id, %s,currency_id, date_maturity, partner_id,
                     blocked, credit, debit, ref, account_id,
                     %s, (%s) AS date, %s, amount_currency, quantity, product_id, company_id
                   FROM account_move_line
                   WHERE account_id IN %s
                     AND ''' + query_line + ''')
                     ''', (new_journal.id, period.id, period.date_start, move_id, tuple(account_ids),))
            self.invalidate_cache(cr, uid, context=context)

        #3. report of the accounts with defferal method == 'balance'
        cr.execute('''
            SELECT a.id
            FROM account_account a
            LEFT JOIN account_account_type t ON (a.user_type_id = t.id)
            WHERE NOT a.deprecated
              AND a.internal_type not in ('view', 'consolidation')
              AND a.company_id = %s
              AND t.close_method = %s''', (company_id, 'balance', ))
        account_ids = map(lambda x: x[0], cr.fetchall())

        query_1st_part = """
                INSERT INTO account_move_line (
                     debit, credit, name, date, move_id, journal_id, period_id,
                     account_id, currency_id, amount_currency, company_id,date_maturity) VALUES
        """
        query_2nd_part = ""
        query_2nd_part_args = []
        
        #++
        query_3nd_part = ""
        query_3nd_part_args = []
        utilidad = 0.0        
        
        for account in obj_acc_account.browse(cr, uid, account_ids, context={'fiscalyear': fy_id}):
            company_currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id
            if not currency_obj.is_zero(cr, uid, company_currency_id, abs(account.balance)):
                if query_2nd_part:
                    query_2nd_part += ','
                query_2nd_part += "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

                query_2nd_part_args += (account.balance > 0 and account.balance or 0.0,

                       account.balance < 0 and -account.balance or 0.0,
                       data[0].report_name,
                       period.date_start,
                       move_id,
                       new_journal.id,
                       period.id,
                       account.id,
                       account.currency_id and account.currency_id.id or None,
                       account.foreign_balance if account.currency_id else 0.0,
                       account.company_id.id,
                       period.date_start
                       )
        if query_2nd_part:
            cr.execute(query_1st_part + query_2nd_part, tuple(query_2nd_part_args))
            self.invalidate_cache(cr, uid, context=context)
            
        #Calcula la utilidad o perdida
        utilidad = 0.0
        cr.execute('''
	            SELECT sum(debit-credit)
	            FROM account_move_line
	            WHERE move_id = %s''', (move_id, ))
	    
        res = cr.fetchone()   	
        if res:
           utilidad = res[0]
                               
        if utilidad != 0.0:        
           if utilidad > 0:
              cuenta = new_journal.default_debit_account_id.id
           elif utilidad < 0:
              cuenta = new_journal.default_credit_account_id.id
                      
           #obj_acc_move_line.write(cr, uid, [move_id], vals, context=context)
           query_3nd_part += "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
           query_3nd_part_args += (utilidad < 0 and -utilidad or 0.0,
                                   utilidad > 0 and utilidad or 0.0,                                   
                                   #data[0].report_name,
                                   'Utilidad/Perdidad acumulada' ,
                                   period.date_start,
                                   move_id,
                                   new_journal.id,
                                   period.id,
                                   cuenta,
                                   None,
                                   0.0,
                                   new_journal.company_id.id,
                                   period.date_start
                                   )                
                               
        if query_3nd_part_args:
           cr.execute(query_1st_part + query_3nd_part, tuple(query_3nd_part_args))
           self.invalidate_cache(cr, uid, context=context)            
        
        # contabiliza el asiento
        if move_id:
           obj_acc_move.browse(cr, uid, move_id, context=context).post()
        
        #reconcile all the move.line of the opening move
        ids = obj_acc_move_line.search(cr, uid, [('journal_id', '=', new_journal.id),
            ('period_id.fiscalyear_id','=',new_fyear.id)])
        if ids:
            reconcile_id = _reconcile_fy_closing(cr, uid, ids, context=context)
            #set the creation date of the reconcilation at the first day of the new fiscalyear, in order to have good figures in the aged trial balance
            self.pool.get('account.full.reconcile').write(cr, uid, [reconcile_id], {'create_date': new_fyear.date_start}, context=context)

        #create the journal.period object and link it to the old fiscalyear
        new_period = data[0].period_id.id
        ids = obj_acc_journal_period.search(cr, uid, [('journal_id', '=', new_journal.id), ('period_id', '=', new_period)])
        if not ids:
            ids = [obj_acc_journal_period.create(cr, uid, {
                   'name': (new_journal.name or '') + ':' + (period.code or ''),
                   'journal_id': new_journal.id,
                   'period_id': period.id
               })]
        cr.execute('UPDATE account_fiscalyear ' \
                    'SET end_journal_period_id = %s ' \
                    'WHERE id = %s', (ids[0], old_fyear.id))
        obj_acc_fiscalyear.invalidate_cache(cr, uid, ['end_journal_period_id'], [old_fyear.id], context=context)

        return {'type': 'ir.actions.act_window_close'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
