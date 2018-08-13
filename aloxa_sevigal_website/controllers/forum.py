# -*- coding: utf-8 -*-

import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import simplejson

from openerp import tools
from openerp import SUPERUSER_ID
from openerp.osv import osv, fields
from openerp.addons.web import http
from openerp.addons.web.controllers.main import login_redirect
from openerp.addons.web.http import request
from openerp.addons.website.controllers.main import Website as controllers
from openerp.addons.website.models.website import slug
import openerp.addons.website_forum.controllers.main as forum


# Really crazy! Reimplement all forum class O_o
class WebsiteForum(forum.WebsiteForum):
    _post_per_page = 10
    _user_per_page = 30

    #def _get_notifications(self):
    #    cr, uid, context = request.cr, request.uid, request.context
    #    Message = request.registry['mail.message']
    #    badge_st_id = request.registry['ir.model.data'].xmlid_to_res_id(cr, uid, 'gamification.mt_badge_granted')
    #    if badge_st_id:
    #        msg_ids = Message.search(cr, uid, [('subtype_id', '=', badge_st_id), ('to_read', '=', True)], context=context)
    #        msg = Message.browse(cr, uid, msg_ids, context=context)
    #    else:
    #        msg = list()
    #    return msg

    def _prepare_forum_values(self, forum=None, **kwargs):
        user = request.registry['res.users'].browse(request.cr, request.uid, request.uid, context=request.context)
        values = {
            'user': user,
            'is_public_user': user.id == request.website.user_id.id,
            'notifications': list(), #self._get_notifications(),
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

    # User and validation
    # --------------------------------------------------

    @http.route('/forum/send_validation_email', type='json', auth='user', website=True)
    def send_validation_email(self, forum_id=None, **kwargs):
        request.registry['res.users'].send_forum_validation_email(request.cr, request.uid, request.uid, forum_id=forum_id, context=request.context)
        request.session['validation_email_sent'] = True
        return True

    @http.route('/forum/validate_email', type='http', auth='public', website=True)
    def validate_email(self, token, id, email, forum_id=None, **kwargs):
        if forum_id:
            try:
                forum_id = int(forum_id)
            except ValueError:
                forum_id = None
        done = request.registry['res.users'].process_forum_validation_token(request.cr, request.uid, token, int(id), email, forum_id=forum_id, context=request.context)
        if done:
            request.session['validation_email_done'] = True
        if forum_id:
            return request.redirect("/" % int(forum_id))
        return request.redirect('/')

    @http.route('/forum/validate_email/close', type='json', auth='public', website=True)
    def validate_email_done(self):
        request.session['validation_email_done'] = False
        return True

    # Forum
    # --------------------------------------------------

    @http.route(['/forum'], type='http', auth="public", website=True)
    def forum(self, **kwargs):
        return request.redirect('/')

    @http.route('/forum/new', type='http', auth="user", methods=['POST'], website=True)
    def forum_create(self, forum_name="New Forum", **kwargs):
        return request.redirect('/')

    @http.route('/forum/notification_read', type='json', auth="user", methods=['POST'], website=True)
    def notification_read(self, **kwargs):
        request.registry['mail.message'].set_message_read(request.cr, request.uid, [int(kwargs.get('notification_id'))], read=True, context=request.context)
        return True

    @http.route(['/forum/<model("forum.forum"):forum>',
                 '/forum/<model("forum.forum"):forum>/page/<int:page>',
                 '''/forum/<model("forum.forum"):forum>/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/questions''',
                 '''/forum/<model("forum.forum"):forum>/tag/<model("forum.tag", "[('forum_id','=',forum[0])]"):tag>/questions/page/<int:page>''',
                 ], type='http', auth="public", website=True)
    def questions(self, forum, tag=None, page=1, filters='all', sorting='date', search='', **post):
        return request.redirect('/')

    @http.route(['/forum/<model("forum.forum"):forum>/faq'], type='http', auth="public", website=True)
    def forum_faq(self, forum, **post):
        return request.redirect('/')

    @http.route('/forum/get_tags', type='http', auth="public", methods=['GET'], website=True)
    def tag_read(self, q='', l=25, t='texttext', **post):
        data = request.registry['forum.tag'].search_read(
            request.cr,
            request.uid,
            domain=[('name', '=ilike', (q or '') + "%")],
            fields=['id', 'name'],
            limit=int(l),
            context=request.context
        )
        if t == 'texttext':
            # old tag with texttext - Retro for V8 - #TODO Remove in master
            data = [tag['name'] for tag in data]
        return simplejson.dumps(data)

    @http.route(['/forum/<model("forum.forum"):forum>/tag'], type='http', auth="public", website=True)
    def tags(self, forum, page=1, **post):
        return request.redirect('/')

    # Questions
    # --------------------------------------------------

    @http.route(['/forum/<model("forum.forum"):forum>/ask'], type='http', auth="public", website=True)
    def question_ask(self, forum, **post):
        return request.redirect('/')

    @http.route('/forum/<model("forum.forum"):forum>/question/new', type='http', auth="user", methods=['POST'], website=True)
    def question_create(self, forum, **post):
        cr, uid, context = request.cr, request.uid, request.context
        Tag = request.registry['forum.tag']
        Forum = request.registry['forum.forum']
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

        new_question_id = request.registry['forum.post'].create(
            request.cr, request.uid, {
                'forum_id': forum.id,
                'name': post.get('question_name'),
                'content': post.get('content'),
                'tag_ids': question_tag_ids[forum.id],
            }, context=context)
        return werkzeug.utils.redirect("/mensaje/%s" % new_question_id)

    @http.route(['''/forum/<model("forum.forum"):forum>/question/<model("forum.post", "[('forum_id','=',forum[0]),('parent_id','=',False)]"):question>'''], type='http', auth="public", website=True)
    def question(self, forum, question, **post):
        cr, uid, context = request.cr, request.uid, request.context

        # Hide posts from abusers (negative karma), except for moderators
        if not question.can_view:
            raise werkzeug.exceptions.NotFound()

        # increment view counter
        request.registry['forum.post'].set_viewed(cr, SUPERUSER_ID, [question.id], context=context)

        if question.parent_id:
            redirect_url = "/mensaje/%s" % slug(question.parent_id)
            return werkzeug.utils.redirect(redirect_url, 301)

        redirect_url = "/mensaje/%s" % slug(question)
        return werkzeug.utils.redirect(redirect_url, 301)

    # Cambiamos el concepto de 'favorito' por el de 'archivado'
    # Sobreescibimos el metodo anterior para que no haga nada
    @http.route('/forum/<model("forum.forum"):forum>/question/<model("forum.post"):question>/toggle_favourite', type='json', auth="user", methods=['POST'], website=True)
    def question_toggle_favorite(self, forum, question, **post):
        return ""
    # Creamos al nueva ruta con un nombre que haga referencia a la accion de cara al usuario
    @http.route('/forum/<model("forum.forum"):forum>/question/<model("forum.post"):question>/toggle_archived', type='json', auth="user", methods=['POST'], website=True)
    def question_toggle_archived(self, forum, question, **post):
        if not request.session.uid:
            return {'error': 'anonymous_user'}
        # TDE: add check for not public
        favourite = False if question.user_favourite else True
        if favourite:
            favourite_ids = [(4, request.uid)]
        else:
            favourite_ids = [(3, request.uid)]

        question.sudo().write({'favourite_ids': favourite_ids}, context=request.context)
        return favourite


    @http.route('/forum/<model("forum.forum"):forum>/question/<model("forum.post"):question>/ask_for_close', type='http', auth="user", methods=['POST'], website=True)
    def question_ask_for_close(self, forum, question, **post):
        cr, uid, context = request.cr, request.uid, request.context
        redirect_url = "cerrar/pregunta/%s" % slug(question)
        return werkzeug.utils.redirect(redirect_url, 301)

    @http.route('/forum/<model("forum.forum"):forum>/question/<model("forum.post"):question>/edit_answer', type='http', auth="user", website=True)
    def question_edit_answer(self, forum, question, **kwargs):
        for record in question.child_ids:
            if record.create_uid.id == request.uid:
                answer = record
                break
        return werkzeug.utils.redirect("/forum/%s/post/%s/edit" % (slug(forum), slug(answer)))

    @http.route('/forum/<model("forum.forum"):forum>/question/<model("forum.post"):question>/close', type='http', auth="user", methods=['POST'], website=True)
    def question_close(self, forum, question, **post):
        request.registry['forum.post'].close(request.cr, request.uid, [question.id], reason_id=int(post.get('reason_id', False)), context=request.context)
        return werkzeug.utils.redirect("/mensaje/%s" % slug(question))

    @http.route('/forum/<model("forum.forum"):forum>/question/<model("forum.post"):question>/reopen', type='http', auth="user", methods=['POST'], website=True)
    def question_reopen(self, forum, question, **kwarg):
        request.registry['forum.post'].reopen(request.cr, request.uid, [question.id], context=request.context)
        return werkzeug.utils.redirect("/mensaje/%s" % slug(question))

    @http.route('/forum/<model("forum.forum"):forum>/question/<model("forum.post"):question>/delete', type='http', auth="user", methods=['POST'], website=True)
    def question_delete(self, forum, question, **kwarg):
        request.registry['forum.post'].write(request.cr, request.uid, [question.id], {'active': False}, context=request.context)
        return werkzeug.utils.redirect("/mensaje/%s" % slug(question))

    @http.route('/forum/<model("forum.forum"):forum>/question/<model("forum.post"):question>/undelete', type='http', auth="user", methods=['POST'], website=True)
    def question_undelete(self, forum, question, **kwarg):
        request.registry['forum.post'].write(request.cr, request.uid, [question.id], {'active': True}, context=request.context)
        return werkzeug.utils.redirect("/mensaje/%s" % slug(question))

    # Post
    # --------------------------------------------------

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/new', type='http', auth="public", website=True)
    def post_new(self, forum, post, **kwargs):
        if not request.session.uid:
            return login_redirect()
        cr, uid, context = request.cr, request.uid, request.context
        user = request.registry['res.users'].browse(cr, SUPERUSER_ID, uid, context=context)
        if not user.email or not tools.single_email_re.match(user.email):
            return werkzeug.utils.redirect("/forum/%s/user/%s/edit?email_required=1" % (slug(forum), uid))
        request.registry['forum.post'].create(
            request.cr, request.uid, {
                'forum_id': forum.id,
                'parent_id': post.id,
                'content': kwargs.get('content'),
            }, context=request.context)
        return werkzeug.utils.redirect("/mensaje/%s" % slug(post))

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/comment', type='http', auth="public", website=True)
    def post_comment(self, forum, post, **kwargs):
        if not request.session.uid:
            return login_redirect()
        question = post.parent_id if post.parent_id else post
        cr, uid, context = request.cr, request.uid, request.context
        if kwargs.get('comment') and post.forum_id.id == forum.id:
            # TDE FIXME: check that post_id is the question or one of its answers
            request.registry['forum.post'].message_post(
                cr, uid, post.id,
                body=kwargs.get('comment'),
                type='comment',
                subtype='mt_comment',
                context=dict(context, mail_create_nosubscribe=True))
        return werkzeug.utils.redirect("/mensaje/%s" % slug(question))

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/toggle_correct', type='json', auth="public", website=True)
    def post_toggle_correct(self, forum, post, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        if post.parent_id is False:
            return request.redirect('/')
        if not request.session.uid:
            return {'error': 'anonymous_user'}

        # set all answers to False, only one can be accepted
        request.registry['forum.post'].write(cr, uid, [c.id for c in post.parent_id.child_ids if not c.id == post.id], {'is_correct': False}, context=context)
        request.registry['forum.post'].write(cr, uid, [post.id], {'is_correct': not post.is_correct}, context=context)
        return post.is_correct

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/delete', type='http', auth="user", methods=['POST'], website=True)
    def post_delete(self, forum, post, **kwargs):
        question = post.parent_id
        request.registry['forum.post'].unlink(request.cr, request.uid, [post.id], context=request.context)
        if question:
            werkzeug.utils.redirect("/mensaje/%s" % slug(question))
        return request.redirect('/')

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/edit', type='http', auth="user", website=True)
    def post_edit(self, forum, post, **kwargs):
        tag_version = kwargs.get('tag_type', 'texttext')
        if tag_version == "texttext":  # old version - retro v8 - #TODO Remove in master
            tags = ""
            for tag_name in post.tag_ids:
                tags += tag_name.name + ","
        elif tag_version == "select2":  # new version
            tags = [dict(id=tag.id, name=tag.name) for tag in post.tag_ids]
            tags = simplejson.dumps(tags)
        values = self._prepare_forum_values(forum=forum)

        values.update({
            'tags': tags,
            'post': post,
            'is_answer': bool(post.parent_id),
            'searches': kwargs,
            'header': {'type': post.parent_id.tipo, 'ask_hide':True},
        })
        return request.website.render("aloxa_sevigal_website.edit_post", values)

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/edition', type='http', auth="user", website=True)
    def post_edit_retro(self, forum, post, **kwargs):
        # This function is only there for retrocompatibility between old template using texttext and template using select2
        # It should be removed into master  #TODO JKE: remove in master all condition with tag_type
        kwargs.update(tag_type="select2")
        return self.post_edit(forum, post, **kwargs)

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/save', type='http', auth="user", methods=['POST'], website=True)
    def post_save(self, forum, post, **kwargs):
        cr, uid, context = request.cr, request.uid, request.context
        question_tags = []
        Tag = request.registry['forum.tag']
        Forum = request.registry['forum.forum']
        tag_version = kwargs.get('tag_type', 'texttext')

        vals = {
            'name': kwargs.get('question_name'),
            'content': kwargs.get('content'),
        }
        if tag_version == "texttext":  # old version - retro v8 - #TODO Remove in master
            if kwargs.get('question_tag') and kwargs.get('question_tag').strip('[]'):
                tags = kwargs.get('question_tag').strip('[]').replace('"', '').split(",")
                for tag in tags:
                    tag_ids = Tag.search(cr, uid, [('name', '=', tag)], context=context)
                    if tag_ids:
                        question_tags += tag_ids
                    else:
                        new_tag = Tag.create(cr, uid, {'name': tag, 'forum_id': forum.id}, context=context)
                        question_tags.append(new_tag)
                vals['tag_ids'] = [(6, 0, question_tags)]
        elif tag_version == "select2":  # new version
            vals['tag_ids'] = Forum._tag_to_write_vals(cr, uid, [forum.id], kwargs.get('question_tag', ''), context)[forum.id]

        request.registry['forum.post'].write(cr, uid, [post.id], vals, context=context)
        question = post.parent_id if post.parent_id else post
        return werkzeug.utils.redirect("/mensaje/%s" % slug(question))

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/upvote', type='json', auth="public", website=True)
    def post_upvote(self, forum, post, **kwargs):
        if not request.session.uid:
            return {'error': 'anonymous_user'}
        if request.uid == post.create_uid.id:
            return {'error': 'own_post'}
        upvote = True if not post.user_vote > 0 else False
        return request.registry['forum.post'].vote(request.cr, request.uid, [post.id], upvote=upvote, context=request.context)

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/downvote', type='json', auth="public", website=True)
    def post_downvote(self, forum, post, **kwargs):
        if not request.session.uid:
            return {'error': 'anonymous_user'}
        if request.uid == post.create_uid.id:
            return {'error': 'own_post'}
        upvote = True if post.user_vote < 0 else False
        return request.registry['forum.post'].vote(request.cr, request.uid, [post.id], upvote=upvote, context=request.context)

    # User
    # --------------------------------------------------

    @http.route(['/forum/<model("forum.forum"):forum>/users',
                 '/forum/<model("forum.forum"):forum>/users/page/<int:page>'],
                type='http', auth="public", website=True)
    def users(self, forum, page=1, **searches):
        return request.redirect('/')

    @http.route(['/forum/<model("forum.forum"):forum>/partner/<int:partner_id>'], type='http', auth="public", website=True)
    def open_partner(self, forum, partner_id=0, **post):
        return request.redirect('/')

    @http.route(['/forum/user/<int:user_id>/avatar'], type='http', auth="public", website=True)
    def user_avatar(self, user_id=0, **post):
        cr, uid, context = request.cr, request.uid, request.context
        response = werkzeug.wrappers.Response()
        User = request.registry['res.users']
        Website = request.registry['website']
        user = User.browse(cr, SUPERUSER_ID, user_id, context=context)
        if not user.exists() or (user_id != request.session.uid and user.karma < 1):
            return Website._image_placeholder(response)
        return Website._image(cr, SUPERUSER_ID, 'res.users', user.id, 'image', response)

    @http.route(['/forum/<model("forum.forum"):forum>/user/<int:user_id>'], type='http', auth="public", website=True)
    def open_user(self, forum, user_id=0, **post):
        return request.redirect('/')

    @http.route('/forum/<model("forum.forum"):forum>/user/<model("res.users"):user>/edit', type='http', auth="user", website=True)
    def edit_profile(self, forum, user, **kwargs):
        return request.redirect('/')

    @http.route('/forum/<model("forum.forum"):forum>/user/<model("res.users"):user>/save', type='http', auth="user", methods=['POST'], website=True)
    def save_edited_profile(self, forum, user, **kwargs):
        return request.redirect('/')

    # Badges
    # --------------------------------------------------

    @http.route('/forum/<model("forum.forum"):forum>/badge', type='http', auth="public", website=True)
    def badges(self, forum, **searches):
        return request.redirect('/')

    @http.route(['''/forum/<model("forum.forum"):forum>/badge/<model("gamification.badge"):badge>'''], type='http', auth="public", website=True)
    def badge_users(self, forum, badge, **kwargs):
        return request.redirect('/')

    # Messaging
    # --------------------------------------------------

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/comment/<model("mail.message"):comment>/convert_to_answer', type='http', auth="user", methods=['POST'], website=True)
    def convert_comment_to_answer(self, forum, post, comment, **kwarg):
        new_post_id = request.registry['forum.post'].convert_comment_to_answer(request.cr, request.uid, comment.id, context=request.context)
        if not new_post_id:
            return werkzeug.utils.redirect("/forum/%s" % slug(forum))
        post = request.registry['forum.post'].browse(request.cr, request.uid, new_post_id, context=request.context)
        question = post.parent_id if post.parent_id else post
        return werkzeug.utils.redirect("/mensaje/%s" % slug(question))

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/convert_to_comment', type='http', auth="user", methods=['POST'], website=True)
    def convert_answer_to_comment(self, forum, post, **kwarg):
        question = post.parent_id
        new_msg_id = request.registry['forum.post'].convert_answer_to_comment(request.cr, request.uid, post.id, context=request.context)
        if not new_msg_id:
            return request.redirect('/')
        return werkzeug.utils.redirect("/mensaje/%s" % slug(question))

    @http.route('/forum/<model("forum.forum"):forum>/post/<model("forum.post"):post>/comment/<model("mail.message"):comment>/delete', type='json', auth="user", website=True)
    def delete_comment(self, forum, post, comment, **kwarg):
        if not request.session.uid:
            return {'error': 'anonymous_user'}
        return request.registry['forum.post'].unlink_comment(request.cr, request.uid, post.id, comment.id, context=request.context)
