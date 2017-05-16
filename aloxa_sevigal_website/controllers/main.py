# -*- coding: utf-8 -*-

import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import simplejson

from openerp import http, models, api, exceptions, SUPERUSER_ID
from openerp.http import request
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import content_disposition
#from openerp.addons.jsonrpc_keys import jsonrpckeys
from . import utils
import json
import pytz
import datetime
import openerp.addons.web.controllers.main as webmain
import logging
_logger = logging.getLogger(__name__)


class SevigalWebsite(webmain.Home):
    _post_per_page = 10
    _user_per_page = 30

    def _login_redirect(self):
        return http.redirect("/entrar")

    def _get_notifications(self):
        cr, uid, context = request.cr, request.uid, request.context
        Message = request.registry['mail.message']
        badge_st_id = request.registry['ir.model.data'].xmlid_to_res_id(cr, uid, 'gamification.mt_badge_granted')
        if badge_st_id:
            msg_ids = Message.search(cr, uid, [('subtype_id', '=', badge_st_id), ('to_read', '=', True)], context=context)
            msg = Message.browse(cr, uid, msg_ids, context=context)
        else:
            msg = list()
        return msg

    def _prepare_forum_values(self, forum=None, **kwargs):
        current_user = request.registry['res.users'].browse(request.cr, request.uid, request.uid, context=request.context)
        values = {
            'user': current_user,
            'is_public_user': current_user.id == request.website.user_id.id,
            'notifications': self._get_notifications(),
            'header': kwargs.get('header', dict()),
            'searches': kwargs.get('searches', dict()),
            'validation_email_sent': request.session.get('validation_email_sent', False),
            'validation_email_done': request.session.get('validation_email_done', False),
        }
        if forum:
            values['forum'] = forum
        elif kwargs.get('forum_id'):
            values['forum'] = request.registry['forum.forum'].browse(request.cr, request.uid, kwargs.pop('forum_id'), context=request.context)
        values.update(kwargs)
        return values

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        webmain.ensure_db()

        redirect = '/'
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = SUPERUSER_ID

        values = request.params.copy()
        values['redirect'] = redirect

        try:
            values['databases'] = http.db_list()
        except exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            if uid is not False:
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = "Wrong login/password"
        if request.env.ref('web.login', False):
            return request.render('web.login', values)
        else:
            # probably not an odoo compatible database
            error = 'Unable to login on database %s' % request.session.db
            return werkzeug.utils.redirect('/web/database/selector?error=%s' % error, 303)

    @http.route('/', auth="user", type="http")
    def index(self, **post):
        if not request.session.uid:
            return self._login_redirect()

        cr, uid, context = request.cr, request.uid, request.context
        User = request.registry['res.users']
        Post = request.registry['forum.post']
        Vote = request.registry['forum.post.vote']
        Activity = request.registry['mail.message']
        Followers = request.registry['mail.followers']
        Data = request.registry["ir.model.data"]

        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        user_ids = [current_user.id]
        partner_ids = [current_user.partner_id.id]
        for user_child in childs_users:
            user_ids.append(user_child.id)
            partner_ids.append(user_child.partner_id.id)

        if not current_user.exists():
            return self._login_redirect()
        forum = request.env['sevigal.opciones'].search([], limit=1).foro_notificaciones_id
        values = self._prepare_forum_values(forum=forum, searches={}, header={'type':'Index'}, **post)

        # questions and answers by user
        user_question_ids = Post.search(cr, uid, [
                ('parent_id', '=', False),
                ('forum_id', '=', forum.id), 
                ('create_uid', 'in', user_ids),
            ], order='create_date desc', context=context)

        # Telefonos
        phones = []
        partners = request.env['res.partner'].search([('id', 'in', partner_ids)])
        for partner_child in partners:
            phones.append(partner_child.telefono_ids)

        # limit length of visible posts by default for performance reasons, except for the high
        # karma users (not many of them, and they need it to properly moderate the forum)
        post_display_limit = None
        if current_user.karma < forum.karma_unlink_all:
            post_display_limit = 20

        user_questions = Post.browse(cr, uid, user_question_ids[:post_display_limit], context=context)
        user_answer_ids = Post.search(cr, uid, [
                ('parent_id', '!=', False),
                ('forum_id', '=', forum.id), ('create_uid', 'in', user_ids),
            ], order='create_date desc', context=context)
        count_user_answers = len(user_answer_ids)
        user_answers = Post.browse(cr, uid, user_answer_ids[:post_display_limit], context=context)

        # showing questions which user following
#         obj_ids = Followers.search(cr, SUPERUSER_ID, [('res_model', '=', 'forum.post'), ('partner_id', 'in', partner_ids)], context=context)
#         post_ids = [follower.res_id for follower in Followers.browse(cr, SUPERUSER_ID, obj_ids, context=context)]
#         que_ids = Post.search(cr, uid, [('id', 'in', post_ids), ('forum_id', '=', forum.id), ('parent_id', '=', False)], context=context)
#         followed = Post.browse(cr, uid, que_ids, context=context)

        #showing Archived questions of user.
        fav_que_ids = Post.search(cr, uid, [('favourite_ids', '=', current_user.id), ('forum_id', '=', forum.id), ('parent_id', '=', False)], context=context)
        favourite = Post.browse(cr, uid, fav_que_ids, context=context)

        #votes which given on users questions and answers.
        data = Vote.read_group(cr, uid, [('forum_id', '=', forum.id), ('recipient_id', '=', current_user.id)], ["vote"], groupby=["vote"], context=context)
        up_votes, down_votes = 0, 0
        for rec in data:
            if rec['vote'] == '1':
                up_votes = rec['vote_count']
            elif rec['vote'] == '-1':
                down_votes = rec['vote_count']

        #Votes which given by users on others questions and answers.
        post_votes = Vote.search(cr, uid, [('user_id', 'in', user_ids)], context=context)
        vote_ids = Vote.browse(cr, uid, post_votes, context=context)

        #activity by user.
        model, comment = Data.get_object_reference(cr, uid, 'mail', 'mt_comment')
        activity_ids = Activity.search(cr, uid, [('res_id', 'in', user_question_ids+user_answer_ids), ('model', '=', 'forum.post'), ('subtype_id', '!=', comment)], order='date DESC', limit=100, context=context)
        activities = Activity.browse(cr, uid, activity_ids, context=context)

        posts = {}
        for act in activities:
            posts[act.res_id] = True
        posts_ids = Post.browse(cr, uid, posts.keys(), context=context)
        posts = dict(map(lambda x: (x.id, (x.parent_id or x, x.parent_id and x or False)), posts_ids))

        # TDE CLEANME MASTER: couldn't it be rewritten using a 'menu' key instead of one key for each menu ?
        post['my_profile'] = True

        values.update({
            'uid': uid,
            'main_object': current_user,
            'searches': post,
            'answers': user_answers,
            'count_answers': count_user_answers,
            #'followed': followed,
            'favourite': favourite,
            'up_votes': up_votes,
            'down_votes': down_votes,
            'activities': activities,
            'posts': posts,
            'vote_post': vote_ids,
            'phones': phones
        })

        return request.website.render("aloxa_sevigal_website.info", values)

    @http.route(['/calendario'], auth="user", type='http', website=True)
    def forum_calendar(self, **post):
        if not request.session.uid:
            return self._login_redirect()

        forum = request.env['sevigal.opciones'].search([], limit=1).foro_notificaciones_id
        values = self._prepare_forum_values(forum=forum, searches={}, header={'type':'Calendario'}, **post)

        # FIXME: Deprecated: Usada esta forma por no encontrar otra mejor
        ua = request.httprequest.environ.get('HTTP_USER_AGENT', '').lower()
        if any(x in ua for x in ('android', 'iphone', 'blackberry')):
            return request.website.render("aloxa_sevigal_website.calendario_mobile", values)
        else:
            return request.website.render("aloxa_sevigal_website.calendario", values)

    @http.route(['/facturas'], auth="user", type='http', website=True)
    def facturas(self, **post):
        if not request.session.uid:
            return self._login_redirect()

        cr, uid, context = request.cr, request.uid, request.context
        forum = request.env['sevigal.opciones'].search([], limit=1).foro_notificaciones_id
        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)

        # Current Invoice
        domain = [('partner_id','in',partner_ids),('state','=','open')]
        invoice = request.env['account.analytic.account'].search(domain, limit=1)
        invoice_lines = invoice.recurring_invoice_line_ids
        recurring = invoice.recurring_invoices
        next_date = invoice.recurring_next_date
        # History
        domain = [('partner_id', 'in', partner_ids)]
        history_lines = request.env['account.invoice'].search(domain, order="date_invoice DESC")

        values = self._prepare_forum_values(forum=forum, searches={}, header={'type':'Factura'}, **post)
        values.update({
            'invoice_lines':invoice_lines,
            'recurring': recurring,
            'next_date': next_date,
            'history_lines': history_lines,
        })
        return request.website.render("aloxa_sevigal_website.facturas", values)

    @http.route(['/factura/descargar'], type='http', auth="user", methods=['GET'], website=True)
    def generate_invoice_report(self, id):
        if not request.session.uid:
            return request.redirect('/facturas')

        cr, uid, context = request.cr, request.uid, request.context
        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)

        domain = [('partner_id', 'in', partner_ids),('id', '=', id)]
        invoice = request.env['account.invoice'].search(domain, limit=1)
        if invoice:
            report_data = request.env['report'].get_pdf(invoice, 'account.report_invoice')
            return request.make_response(
                            report_data, [('Content-Type', 'application/pdf'),
                              ('Content-Disposition',
                               content_disposition('Factura-%s.pdf' % str(invoice.number)))])
        return request.redirect('/facturas')

    @http.route(['/alertas/page/<int:page>',
                 '/servicios/reuniones/page/<int:page>',
                 '/servicios/viajes/page/<int:page>',
                 '/mensajes/page/<int:page>',
                 '''/alertas/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/mensajes''',
                 '''/servicios/reuniones/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/mensajes''',
                 '''/servicios/viajes/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/mensajes''',
                 '''/mensajes/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/mensajes''',
                 '''/alertas/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/mensajes/page/<int:page>''',
                 '''/servicios/reuniones/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/mensajes/page/<int:page>''',
                 '''/servicios/viajes/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/mensajes/page/<int:page>''',
                 '''/mensajes/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/mensajes/page/<int:page>''',
                 '/alertas',
                 '/servicios/reuniones',
                 '/servicios/viajes',
                 '/mensajes'], type='http', auth="user", website=True)
    def forum_page(self, tag=None, page=1, filters='all', sorting='date', search='', **post):
        if not request.session.uid:
            return self._login_redirect()

        cr, uid, context = request.cr, request.uid, request.context
        forum = request.env['sevigal.opciones'].search([], limit=1).foro_notificaciones_id
        Post = request.registry['forum.post']
        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        user_ids = [current_user.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)
            user_ids.append(user_child.id)

        if request.httprequest.path.startswith("/servicios/reuniones"):
            post_type = "Reunion"
            url = "/servicios/reuniones"
        elif request.httprequest.path.startswith("/servicios/viajes"):
            post_type = "Viaje"
            url = "/servicios/viajes"
        elif request.httprequest.path.startswith("/mensajes"):
            post_type = "Mensaje"
            url = "/mensajes"
        else:
            post_type = "Notificacion"
            url = "/alertas"

        if tag:
            url = "%s/tag/%s/mensajes" % (url, slug(tag))

        if post_type == "Mensaje":
            domain = [('forum_id', '=', forum.id), ('parent_id', '=', False), ('state', '=', 'active'), ('create_uid','in',user_ids), ('tipo','=',post_type)]
        else:
            domain = [('forum_id', '=', forum.id), ('parent_id', '=', False), ('state', '=', 'active'), ('partner_id','in',partner_ids), ('tipo','=',post_type)]

        if search:
            domain += ['|', ('name', 'ilike', search), ('content', 'ilike', search)]
        if tag:
            domain += [('tag_ids', 'in', tag.id)]
        if filters == 'unanswered':
            domain += [('child_ids', '=', False)]
        elif filters == 'followed':
            domain += [('message_follower_ids', '=', current_user.partner_id.id)]
        elif filters == 'archived':
            domain += [('favourite_ids', '=', uid)]
        elif filters == 'unread':
            domain += [('views', '=', 0)]
        else:
            filters = 'all'
            # Don't show "arcived" messages (favourites)
            domain += [('favourite_ids', '!=', uid)]

        if sorting == 'answered':
            order = 'child_count desc'
        elif sorting == 'vote':
            order = 'vote_count desc'
        elif sorting == 'date':
            order = 'write_date desc'
        else:
            sorting = 'creation'
            order = 'create_date desc'

        url_args = {}
        if search:
            url_args['search'] = search
        if filters:
            url_args['filters'] = filters
        if sorting:
            url_args['sorting'] = sorting

        question_ids = None
        question_ids_unread = None
        question_count_unread = 0
        question_count = 0
        #if post_type == 'Notificacion':
        #    domain_read = domain+[('views','>',0)]
        #    question_count = Post.search(cr, uid, domain_read, count=True, context=context)
        #    pager = request.website.pager(url=url, total=question_count, page=page,
        #                                  step=self._post_per_page, scope=self._post_per_page,
        #                                  url_args=url_args)
        #    obj_ids = Post.search(cr, uid, domain_read, limit=self._post_per_page, offset=pager['offset'], order=order, context=context)
        #    question_ids = Post.browse(cr, uid, obj_ids, context=context)
        #    
        #    domain_unread = domain+[('views','=',0)]
        #    question_count_unread = Post.search(cr, uid, domain_unread, count=True, context=context)
        #    pager_unread = request.website.pager(url=url, total=question_count, page=page,
        #                                  step=self._post_per_page, scope=self._post_per_page,
        #                                  url_args=url_args)
        #    obj_ids = Post.search(cr, uid, domain_unread, limit=self._post_per_page, offset=pager_unread['offset'], order=order, context=context)
        #    question_ids_unread = Post.browse(cr, uid, obj_ids, context=context)
        #else:
        question_count = Post.search(cr, uid, domain, count=True, context=context)
        pager = request.website.pager(url=url, total=question_count, page=page,
                                      step=self._post_per_page, scope=self._post_per_page,
                                      url_args=url_args)
        obj_ids = Post.search(cr, uid, domain, limit=self._post_per_page, offset=pager['offset'], order=order, context=context)
        question_ids = Post.browse(cr, uid, obj_ids, context=context)

        values = self._prepare_forum_values(forum=forum, searches=post, header={'type':post_type, 'ask_hide': request.httprequest.path.startswith("/alertas")})
        values.update({
            'main_object': tag or forum,
            'question_ids': question_ids,
            'question_ids_unread': question_ids_unread,
            'question_count': question_count,
            'question_count_unread': question_count_unread,
            'pager': pager,
            'tag': tag,
            'filters': filters,
            'sorting': sorting,
            'search': search
        })
        return request.website.render("aloxa_sevigal_website.page_index", values)

    @http.route(['''/mensaje/<model("forum.post", "[('forum_id','=',forum[0]),('parent_id','=',False)]"):question>'''], type='http', auth="user", website=True)
    def question(self, question, **post):
        cr, uid, context = request.cr, request.uid, request.context

        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)

        # Hide posts from abusers (negative karma), except for moderators
        #user = request.env['res.users'].browse([uid])
        if not current_user or not current_user.partner_id:
            raise werkzeug.exceptions.NotFound()
        if not question.can_view and not question.partner_id.id in partner_ids:
            raise werkzeug.exceptions.NotFound()

        forum = request.env['sevigal.opciones'].search([('nombre','=','Default')], limit=1).foro_notificaciones_id

        # increment view counter
        request.registry['forum.post'].set_viewed(cr, SUPERUSER_ID, [question.id], context=context)

        if question.parent_id:
            redirect_url = "/mensaje/%s" % slug(question.parent_id)
            return werkzeug.utils.redirect(redirect_url, 301)

        filters = 'question'
        values = self._prepare_forum_values(forum=forum, searches=post)
        values.update({
            'main_object': question,
            'question': question,
            'header': {'question_data': True, 'type': question.tipo, 'ask_hide': True},
            'filters': filters,
            'reversed': reversed,
        })
        return request.website.render("aloxa_sevigal_website.post_description_full", values)

    @http.route(['/mensajes/preguntar',
                 '/servicios/reuniones/preguntar',
                 '/servicios/viajes/preguntar'], type='http', auth="user", website=True)
    def question_ask(self, **post):
        if not request.session.uid:
            return self._login_redirect()

        if request.httprequest.path.startswith("/servicios/reuniones"):
            post_type = "Reunion"
            url_ask = '/servicios/reuniones/nuevo'
        elif request.httprequest.path.startswith("/servicios/viajes"):
            post_type = "Viaje"
            url_ask = '/servicios/viajes/nuevo'
        else:
            post_type = "Mensaje"
            url_ask = '/mensajes/nuevo'

        forum = request.env['sevigal.opciones'].search([], limit=1).foro_notificaciones_id
        values = self._prepare_forum_values(forum=forum, searches={}, header={'ask_hide': True, 'type': post_type, 'url_ask': url_ask})
        return request.website.render("aloxa_sevigal_website.ask_question", values)

    @http.route(['/mensajes/nuevo',
                 '/servicios/reuniones/nuevo',
                 '/servicios/viajes/nuevo'], type='http', auth="user", methods=['POST'], website=True)
    def question_create(self, **post):
        cr, uid, context = request.cr, request.uid, request.context
        forum = request.env['sevigal.opciones'].search([], limit=1).foro_notificaciones_id
        Tag = request.registry['forum.tag']
        Forum = request.registry['forum.forum']
        #user = request.registry['res.users'].browse(cr, uid, uid, context=context)
        partner_id = request.env['res.users'].browse(uid).partner_id.id
        question_tag_ids = []
        tag_version = post.get('tag_type', 'texttext')
        if tag_version == "texttext":  # TODO Remove in master
            if post.get('question_tags').strip('[]'):
                tags = post.get('question_tags').strip('[]').replace('"', '').split(",")
                for tag in tags:
                    tag_ids = Tag.search(cr, uid, [('name', '=', tag)], context=context)
                    if tag_ids:
                        question_tag_ids.append((4, tag_ids[0]))
                    else:
                        question_tag_ids.append((0, 0, {'name': tag, 'forum_id': forum.id}))
                question_tag_ids = {forum.id: question_tag_ids}
        elif tag_version == "select2":
            question_tag_ids = Forum._tag_to_write_vals(cr, uid, [forum.id], post.get('question_tags', ''), context)

        if request.httprequest.path.startswith("/servicios/reuniones"):
            post_type = "Reunion"
        elif request.httprequest.path.startswith("/servicios/viajes"):
            post_type = "Viaje"
        elif request.httprequest.path.startswith("/mensajes"):
            post_type = "Mensaje"

        # Crear Mensaje Foro
        new_question_id = request.registry['forum.post'].create(
            request.cr, request.uid, {
                'forum_id': forum.id,
                'name': post.get('question_name'),
                'content': post.get('content'),
                'tag_ids': question_tag_ids[forum.id],
                'tipo': post_type,
                'partner_id': partner_id,
            }, context=context)

        # Lanzar captura de mensajes
        request.env['sevigal.aviso'].sudo().obtener_eventos_mensajes()

        return werkzeug.utils.redirect("/mensaje/%s" % new_question_id)

    @http.route('/cerrar/pregunta/<model("forum.post"):question>', 
                type='http', auth="user", methods=['POST'], website=True)
    def question_ask_for_close(self, question, **post):
        cr, uid, context = request.cr, request.uid, request.context
        forum = request.env['sevigal.opciones'].search([], limit=1).foro_notificaciones_id

        Reason = request.registry['forum.post.reason']
        reason_ids = Reason.search(cr, uid, [], context=context)
        reasons = Reason.browse(cr, uid, reason_ids, context)

        values = self._prepare_forum_values(**post)
        values.update({
            'question': question,
            'question': question,
            'forum': forum,
            'reasons': reasons,
            'header': {'type': question.tipo, 'ask_hide':True},
        })
        return request.website.render("aloxa_sevigal_website.close_question", values)

    # JSON-RPC
    @http.route(['/_remove_contact'], type='json', website=True)
    def remove_contact(self, id):
        if not request.session.uid:
            return {'error': 'anonymous_user'}

        cr, uid, context = request.cr, request.uid, request.context
        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)

        phone_line = request.env['sevigal.telefono'].search([('id', '=', id),('partner_id', 'in', partner_ids)], limit=1)
        if phone_line:
            phone_line.unlink()
            return {'success': id}
        else:
            return {'error': 'invalid contact'}

    @http.route(['/_add_contact'], type='json', website=True)
    def add_contact(self, phone, description=None):
        if not request.session.uid:
            return {'error': 'anonymous_user'}

        cr, uid, context = request.cr, request.uid, request.context
        partner_id = request.env['res.users'].browse(uid).partner_id.id
        Model = request.session.model('sevigal.telefono')
        contact_id = Model.create({ 'partner_id':partner_id, 'numero':phone, 'descripcion':description }, request.context)
        return {'success': contact_id} if contact_id else {'error': 'invalid contact'}

    @http.route(['/_get_unread_alerts_count'], type='json', website=True)
    def get_unread_alerts_count(self):
        if not request.session.uid:
            return {'error': 'anonymous_user'}

        cr, uid, context = request.cr, request.uid, request.context
        forum = request.env['sevigal.opciones'].search([], limit=1).foro_notificaciones_id
        Post = request.registry['forum.post']
        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)

        domain = [('forum_id', '=', forum.id), ('parent_id', '=', False), ('state', '=', 'active'), ('partner_id','in',partner_ids), 
                  ('tipo','=','Notificacion'), ('views','=',0)]
        question_count = Post.search(cr, uid, domain, count=True, context=context)
        last_reg = Post.search(cr, uid, domain, limit=1, order='id desc', context=context)

        return {'num':question_count, 'last_id':last_reg[0] if last_reg else -1}

    @http.route(['/calendario/get_events'], type='json', website=True)
    def calendario_get_events(self):
        if not request.session.uid:
            return {'error': 'anonymous_user'}

        cr, uid, context = request.cr, request.uid, request.context
        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)

        events = request.env['calendar.event'].search([('partner_ids','in',partner_ids)])
        result = []
        for event in events:
            last_modif_user = request.env['res.users'].sudo().search([('partner_id', '=', event.message_ids[-1].author_id.id)])
            result.append({
                'title': event.name,
                'start': event.start,
                'end': event.stop if not event.allday else None,
                'allDay': event.allday,
                'id': event.id,
                'color': "#31698A" if last_modif_user.has_group('aloxa_sevigal_secretaria.sevigal_user_group') else "#6DC066"
            })

        return result

    @http.route(['/calendario/uc_event'], type='json', website=True)
    def calendario_update_event(self, id, start, stop, allday, title):
        if not request.session.uid:
            return {'error': 'anonymous_user'}

        cr, uid, context = request.cr, request.uid, request.context
        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        user_ids = [current_user.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)
            user_ids.append(user_child.id)

        if id >= 0:
            event = request.env['calendar.event'].search([('id','=',id),'|',('user_id','in',user_ids),('partner_ids','in',partner_ids)], limit=1)
            event.write({ 'stop':stop, 'start':start, 'allday':allday, 'name': title })
            return {}
        else:
            Model = request.session.model('calendar.event')
            event_id = Model.create({ 'stop':stop, 'start':start, 'allday':allday, 'name':title }, request.context)
            event = Model.browse(event_id)
            event.write({ 'partner_ids':[current_user.partner_id.id] })

            return {'id': event_id}

    @http.route(['/calendario/delete_event'], type='json', website=True)
    def calendario_delete_event(self, id):
        if not request.session.uid:
            return {'error': 'anonymous_user'}

        cr, uid, context = request.cr, request.uid, request.context
        User = request.registry['res.users']
        current_user = User.browse(cr, SUPERUSER_ID, uid, context=context)
        childs_users = request.env['res.users'].search([('partner_id.parent_id', '=', current_user.partner_id.id)])
        partner_ids = [current_user.partner_id.id]
        user_ids = [current_user.id]
        for user_child in childs_users:
            partner_ids.append(user_child.partner_id.id)
            user_ids.append(user_child.id)

        #partner_id = request.env['res.users'].browse(request.uid).partner_id
        event = request.env['calendar.event'].search([
                ('id', '=', id),
                '|', ('user_id', 'in', user_ids),
                ('partner_ids', 'in', partner_ids)
            ], limit=1)
        event.unlink()
        return {}

    # LAMBDA TELEMATICS: Entrada de datos
    # Al no tener usuario se tiene que usar 'sudo()' para escalar permisos.
    #
    # ATRIBUTOS:
    # did - Número por el cual entra una llamada o número de salida de la centralita.
    # src - Número que origina la llamada.
    # dst - Número destino de la llamada.
    # start - Comienzo de la llamada. Formato: yyyy-mm-dd hh:mm:ss sin información de zona horaria.
    # duration - Duración (facturable) en segundos de la llamada.
    #
    # Los atributos "did, src, dst" estarán en formato E164 (en caso de ser numeración geográfica o móvil) 
    # o en formato extensión interna (solamente dígitos).
    #
    @http.route(['/registrar/llamada'], type='json', auth="none", jsonrpckey=True, cors='*')
    def register_call(self, did, src, dst, start, duration):
        user_id = request.jsonrpckey['user']

        # Imprimir Info Debug
        remote_addr = request.httprequest.remote_addr
        _logger.info("[JSON-RPC][REGISTRAR/LLAMADA][%s] -- did: '%s' -- src: '%s' -- dst: '%s' -- start: '%s' -- duration: '%s'" %
                     (remote_addr, did, src, dst, start, duration))

        # Comprobar IP
        #if not remote_addr == '192.168.122.1':
        #    raise Exception('Dirección de origen no permitida')

        # Omitir codigo de pais en el numero de telefono
        num_tlf = did[3:] if did[0] == '+' else did

        # Buscar cliente asociado al numero de telefono
        client_id = request.env['res.partner'].sudo().search([('ref', '=', num_tlf)], limit=1)
        if not client_id:
            raise Exception('Cliente no encontrado')

        # GMT a UTC (Se hace esta guarringada por que desde lambda no envian la fecha en UTC :|)
        local = pytz.timezone("Europe/Madrid");
        naive = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        local_dt = local.localize(naive, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)

        # Registrar Llamada
        new_llam_reg = request.env['crm.phonecall'].sudo(user=user_id).create({
            'partner_id': client_id.id,
            'telefono_emisor': src,
            'date': utc_dt,
            'name': 'Llamada recibida de %s' % src,
            'duration': float(duration)/60.0,
            'partner_mobile': num_tlf
        })
        if not new_llam_reg:
            raise Exception('No se pudo guardar el registro')

        return True
