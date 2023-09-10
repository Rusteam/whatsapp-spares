import os
from datetime import datetime as dt
from typing import Optional

from moysklad import MoySklad
from moysklad.http import MoySkladHttpClient
from moysklad.http.utils import ApiResponse
from moysklad.queries import Query, Search
from moysklad.urls import ApiUrlRegistry
from pydantic import BaseModel, Field  # pylint: disable=no-name-in-module

from bot.scheme.parts import PartOrder


class SupplyPosition(BaseModel):
    quantity: int = Field(..., description="Количество")
    price: float = Field(..., description="Цена")
    vat: int = Field(..., description="НДС")
    discount: float = Field(0, description="Скидка")
    assortment: dict = Field(..., description="Метаданные товара")


class MoySkladSDK(BaseModel):
    login: str = Field(os.getenv("MOYSKLAD_LOGIN"), description="Логин пользователя")
    password: str = Field(
        os.getenv("MOYSKLAD_PASSWORD"), description="Пароль пользователя"
    )
    pos_token: str = Field(
        os.getenv("MOYSKLAD_POS_TOKEN"), description="Токен POS-приложения"
    )
    moy_sklad: MoySklad = None
    methods: ApiUrlRegistry = None
    client: MoySkladHttpClient = None
    meta: dict = {}
    names: dict = {}

    class Config:
        arbitrary_types_allowed = True

    def init(self):
        self.moy_sklad = MoySklad.get_instance(
            login=self.login, password=self.password, pos_token=self.pos_token
        )
        self.methods = self.moy_sklad.get_methods()
        self.client = self.moy_sklad.get_client()

    @staticmethod
    def _find_name_key(keys: list[str]) -> str | None:
        for key in keys:
            if "name" in key.lower():
                return key

    def _get_meta(self, entity: str, name: Optional[str] = None) -> dict:
        if entity in self.meta:
            return self.meta[entity]

        entities = self._list_entities(entity)
        names = [
            one.get("name", one[self._find_name_key(list(one.keys()))])
            for one in entities.rows
        ]
        if name:
            org_meta = [
                org.get("meta") for org in entities.rows if org.get("name") == name
            ]
            if len(org_meta) != 1:
                raise ValueError(
                    f"Найдено {len(org_meta)} сущностей {entity!r} с именем {name!r}: {org_meta}"
                )
            else:
                org_meta = org_meta[0]
        else:
            # Запросить пользовательский ввод
            print_txt = "\n".join([f"{i + 1}. {name}" for i, name in enumerate(names)])
            selected_org = int(
                input(
                    f"Доступные сущности {entity!r}:\n{print_txt}\n"
                    "Выберите сущность (введите порядковый номер): "
                )
            )
            if selected_org < 1 or selected_org > len(entities.rows):
                raise ValueError("Неверный порядковый номер")
            org_meta = entities.rows[selected_org - 1].get("meta")

        self.meta[entity] = org_meta
        return org_meta

    def _create_product(self, part: PartOrder) -> dict:
        """Создать или обновить сущность товара"""
        payload = dict(
            name=part.part_name,
            code=part.part_number,
            article=part.part_number,
            supplier=dict(meta=self.counterparty),
            buyPrice=dict(value=part.price * 100, currency=dict(meta=self.currency)),
        )
        existing = self._list_entities("product", search=part.part_number)

        if len(existing.rows) == 0:
            resp = self._create_entity("product", data=payload)
            print(f"Создана сущность {part.part_number!r}")
            meta = resp.meta
        elif len(existing.rows) == 1:
            meta = existing.rows[0]["meta"]
            # Обновить существующую сущность
            product_id = existing.rows[0].get("id")
            for k, v in payload.items():
                if v != existing.rows[0].get(k):
                    resp = self._update_entity(
                        "product", entity_id=product_id, data=payload
                    )
                    print(f"Обновлен товар {part.part_number!r}")
                    meta = resp.meta
                    break
        else:
            raise ValueError(
                f"Найдено {len(existing.rows)} сущностей с артикулом {part.part_number!r}:\n{existing.rows}"
            )

        return meta

    def __getattr__(self, item):
        """Получить метаданные сущности"""
        if item in [
            "organization",
            "counterparty",
            "currency",
            "store",
            "expenseitem",
            "organization/accounts",
        ]:
            return self._get_meta(item, name=self.names.get(item))
        else:
            return getattr(self, item)

    def _list_entities(
        self, entity: str, search: Optional[str] = None
    ) -> list[ApiResponse]:
        if "/" in entity:
            parent, child = entity.split("/", maxsplit=1)
            parent_id = getattr(self, parent)["href"].split("/")[-1]
            endpoint_url = self.methods.get_relation_list_url(
                entity_name=parent, entity_id=parent_id, relation_entity_name=child
            )
        else:
            endpoint_url = self.methods.get_list_url(entity)
        return self.client.get(
            endpoint_url,
            query=Query(Search(search)) if search else None,
        )

    def create_supply(
        self,
        products: list[PartOrder],
        invoice_date: str = None,
        vat_enabled: bool = False,
        vat_included: bool = False,
        vat_rate: float = 0.0,
    ) -> ApiResponse:
        """Создать приемку из списка товаров

        Args:
            products: список товаров
            invoice_date: дата приемки в формате YYYY-MM-DD
            vat_enabled: с НДС или без
            vat_included: если с НДС, включен ли НДС в цену
            vat_rate: если с НДС, ставка НДС в долях от единицы

        Returns:
            Ответ сервера.
        """
        items_meta = [self._create_product(p) for p in products]
        payload = dict(
            vatEnabled=vat_enabled,
            vatIncluded=vat_included,
            rate=dict(currency=dict(meta=self.currency)),
            organization=dict(meta=self.organization),
            agent=dict(meta=self.counterparty),
            store=dict(meta=self.store),
            moment=self._format_date(invoice_date),
            positions=[
                self._create_supply_position(p, m, vat_rate).dict()
                for p, m in zip(products, items_meta)
            ],
        )
        resp = self._create_entity("supply", data=payload)
        print(f"Создана приемка {resp.data['name']} от {resp.data['moment']}")
        return resp

    def _create_entity(self, entity: str, data: dict):
        return self.client.post(self.methods.get_list_url(entity), data=data)

    def _update_entity(self, entity: str, entity_id: str, data: dict):
        return self.client.put(self.methods.get_by_id_url(entity, entity_id), data=data)

    def _create_supply_position(
        self, part: PartOrder, meta: dict, vat: float = 0.0
    ) -> SupplyPosition:
        return SupplyPosition(
            quantity=part.quantity,
            price=part.price * 100,
            vat=int(vat * 100),
            assortment=dict(meta=meta),
        )

    def _format_date(self, invoice_date: str) -> str:
        if invoice_date:
            return f"{invoice_date} 00:00:00"
        else:
            return dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")

    def create_paymentout(self, total: float, vat_rate: float = 0.0) -> ApiResponse:
        payload = dict(
            organization=dict(meta=self.organization),
            organizationAccount=dict(meta=getattr(self, "organization/accounts")),
            agent=dict(meta=self.counterparty),
            expenseItem=dict(meta=self.expenseitem),
            moment=self._format_date(None),
            rate=dict(currency=dict(meta=self.currency)),
            sum=int(total * 100),
            vatSum=int(total * vat_rate * 100),
        )
        self._create_entity("paymentout", data=payload)
        print(
            f"Создан исходящий платеж {payload['sum'] / 100} {self.names['currency'].value}"
            f" в пользу {self.names['counterparty'].value}"
        )


if __name__ == "__main__":
    from bot.workers import pdf

    order = pdf.PdfOrderEuropeanAutospares(
        "/Users/rustem.galiullin/Downloads/SOW.12436.pdf", checksum=1698.9
    )
    order_items = order.run()

    sklad = MoySkladSDK(
        names=dict(
            organization=None,
            counterparty=order.supplier_name,
            currency=order.currency,
            store="Al Fada Dubai",
        )
    )
    sklad.init()
    parts = [PartOrder(**item) for item in order_items.to_dict(orient="records")]
    sklad.create_supply(
        parts,
        vat_rate=order.vat,
        invoice_date=order_items["invoice_date"].iloc[0],
        vat_included=False,
        vat_enabled=True,
    )
    sklad.create_paymentout(total=order_items["amount"].sum(), vat_rate=order.vat)
